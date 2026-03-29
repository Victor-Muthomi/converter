"""
File management service.

Handles upload validation, safe filename generation, temporary
directory creation, and cleanup — keeping these concerns out of the
routes and converter code.
"""

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from werkzeug.datastructures import FileStorage

from app.utils.exceptions import InvalidFileError
from app.utils.helpers import generate_safe_filename, get_file_extension

logger = logging.getLogger(__name__)


class FileManager:
    """Stateless helpers for file I/O used during conversions."""

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
