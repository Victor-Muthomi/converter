"""
File management service.

Handles upload validation, safe filename generation, temporary
directory creation, and cleanup — keeping these concerns out of the
routes and converter code.
"""

import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Iterable, Optional

from werkzeug.datastructures import FileStorage

from app.utils.exceptions import InvalidFileError
from app.utils.helpers import generate_safe_filename, get_file_extension

logger = logging.getLogger(__name__)


class FileManager:
    """Stateless helpers for file I/O used during conversions."""

    @staticmethod
    def _build_unique_archive_name(filename: str, seen: dict[str, int]) -> str:
        """Return a stable archive member name, suffixing duplicates when needed."""
        path = Path(filename)
        candidate = path.name or "file"

        if candidate not in seen:
            seen[candidate] = 1
            return candidate

        stem = path.stem or "file"
        suffix = path.suffix

        while True:
            duplicate_count = seen[candidate]
            deduped = f"{stem}_{duplicate_count}{suffix}"
            seen[candidate] = duplicate_count + 1
            if deduped not in seen:
                seen[deduped] = 1
                return deduped

    def __init__(self, allowed_extensions: set[str]) -> None:
        """
        Args:
            allowed_extensions: Set of lowercase extensions that are
                                allowed as uploads (e.g. ``{"docx", "pdf", "html"}``).
        """
        self.allowed_extensions = allowed_extensions

    # ── Validation ─────────────────────────────────────────────────────────

    def validate_upload(self, file: Optional[FileStorage]) -> str:
        """
        Validate an uploaded file from a Flask request.

        Checks:
        - file is present and has a filename
        - extension is in the allowed set

        Args:
            file: The ``FileStorage`` object from ``request.files``.

        Returns:
            The original filename.

        Raises:
            InvalidFileError: If anything is wrong with the upload.
        """
        if file is None or file.filename is None or file.filename.strip() == "":
            raise InvalidFileError("No file was provided in the request.")

        ext = get_file_extension(file.filename)

        if ext not in self.allowed_extensions:
            raise InvalidFileError(
                f"File type '.{ext}' is not supported. "
                f"Allowed types: {', '.join(sorted(self.allowed_extensions))}"
            )

        return file.filename

    def validate_uploads(self, files: Iterable[Optional[FileStorage]]) -> list[str]:
        """
        Validate a batch of uploaded files and return their original names.

        Raises:
            InvalidFileError: If no files were supplied or any file is invalid.
        """
        filenames = [self.validate_upload(file) for file in files]

        if not filenames:
            raise InvalidFileError("No file was provided in the request.")

        return filenames

    # ── File operations ────────────────────────────────────────────────────

    def save_upload(self, file: FileStorage, dest_dir: Path) -> Path:
        """
        Save *file* into *dest_dir* with a collision-free name.

        Returns:
            The ``Path`` to the saved file.
        """
        safe_name = generate_safe_filename(file.filename or "upload")
        dest_path = dest_dir / safe_name
        file.save(str(dest_path))
        logger.info("Saved upload → %s", dest_path)
        return dest_path

    def save_uploads(self, files: Iterable[FileStorage], dest_dir: Path) -> list[Path]:
        """Save multiple uploaded files and return their destination paths."""
        return [self.save_upload(file, dest_dir) for file in files]

    def create_archive(
        self,
        files: Iterable[Path],
        dest_dir: Path,
        archive_name: str = "docforge_batch.zip",
        archive_names: Optional[Iterable[str]] = None,
    ) -> Path:
        """
        Bundle converted files into a ZIP archive for batch downloads.

        Returns:
            Path to the generated archive.
        """
        files = list(files)
        archive_names_list = (
            list(archive_names)
            if archive_names is not None
            else [file_path.name for file_path in files]
        )

        if len(files) != len(archive_names_list):
            raise ValueError("Archive file list and archive name list must be the same length.")

        archive_path = dest_dir / generate_safe_filename(archive_name)
        seen_names: dict[str, int] = {}

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path, member_name in zip(files, archive_names_list):
                archive.write(
                    file_path,
                    arcname=self._build_unique_archive_name(member_name, seen_names),
                )

        logger.info("Created archive → %s", archive_path)
        return archive_path

    @staticmethod
    def create_temp_dir(prefix: str = "docforge_") -> Path:
        """
        Create a temporary directory for intermediate conversion artefacts.

        Returns:
            Path to the new temporary directory.
        """
        tmp = Path(tempfile.mkdtemp(prefix=prefix))
        logger.debug("Created temp dir: %s", tmp)
        return tmp

    @staticmethod
    def cleanup(path: Path) -> None:
        """
        Remove a file or directory tree.  Logs but does not raise on
        failure so callers are not interrupted by cleanup errors.
        """
        try:
            if path.is_dir():
                shutil.rmtree(path)
            elif path.is_file():
                path.unlink()
            logger.debug("Cleaned up: %s", path)
        except OSError as exc:
            logger.warning("Cleanup failed for %s: %s", path, exc)
