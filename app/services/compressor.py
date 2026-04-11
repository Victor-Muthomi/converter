"""
Document compression service.

Supported same-format compression targets:
  - PDF  → re-saved with PyMuPDF stream cleanup and image recompression
  - DOCX → repacked as an Office ZIP container
  - PPTX → repacked as an Office ZIP container
"""

import logging
import zipfile
from pathlib import Path
from typing import Optional

from app.utils.exceptions import ConversionError, InvalidFileError
from app.utils.helpers import generate_safe_filename, get_file_extension

logger = logging.getLogger(__name__)

# Default JPEG quality used when recompressing embedded images (0-100).
_IMAGE_QUALITY_MAP = {
    "high": 85,
    "medium": 60,
    "low": 35,
}


class PdfCompressor:
    """Compress supported documents while preserving the original format."""

    def __init__(self, output_dir: Path, engine: Optional["ConversionEngine"] = None) -> None:
        self.output_dir = output_dir
        self.engine = engine

    def _build_output_path(self, input_path: Path) -> Path:
        extension = get_file_extension(input_path.name)
        stem = input_path.stem
        return self.output_dir / generate_safe_filename(
            f"{stem}_compressed.{extension}"
        )

    def _compress_pdf(self, input_path: Path, quality: str) -> Path:
        """Compress a PDF and return the resulting PDF path."""
        output_path = self._build_output_path(input_path)

        try:
            import fitz  # noqa: PLC0415
        except ImportError as exc:
            raise ConversionError(
                "PyMuPDF is not installed. Run: pip install PyMuPDF"
            ) from exc

        image_quality = _IMAGE_QUALITY_MAP.get(quality, _IMAGE_QUALITY_MAP["medium"])

        logger.info(
            "Compressing '%s' (quality=%s, jpeg=%d) → %s",
            input_path.name,
            quality,
            image_quality,
            output_path.name,
        )

        try:
            doc = fitz.open(str(input_path))

            # Re-compress all embedded images to the requested JPEG quality.
            for page in doc:
                for img in page.get_images(full=True):
                    xref = img[0]
                    try:
                        doc.update_stream(
                            xref,
                            fitz.Pixmap(doc, xref).tobytes("jpeg", quality=image_quality),
                        )
                    except Exception:
                        # Skip images that can't be recompressed (e.g. masks).
                        pass

            doc.save(
                str(output_path),
                garbage=4,       # remove unused objects + compact xref
                deflate=True,    # zlib-compress all streams
                clean=True,      # sanitise content streams
                linear=True,     # optimise for fast web viewing
            )
            doc.close()
        except Exception as exc:
            raise ConversionError(f"PDF compression failed: {exc}") from exc

        if not output_path.exists():
            raise ConversionError("Compressed file was not created.")

        original_kb = input_path.stat().st_size / 1024
        compressed_kb = output_path.stat().st_size / 1024
        saved_pct = 100 * (1 - compressed_kb / original_kb) if original_kb else 0
        logger.info(
            "Compression complete: %.1f KB → %.1f KB (%.1f%% saved)",
            original_kb,
            compressed_kb,
            saved_pct,
        )

        return output_path

    def _compress_office_archive(self, input_path: Path) -> Path:
        """Repack Office ZIP containers with maximum deflate compression."""
        output_path = self._build_output_path(input_path)

        logger.info("Repacking '%s' → %s", input_path.name, output_path.name)

        try:
            with zipfile.ZipFile(input_path, "r") as source_archive:
                with zipfile.ZipFile(
                    output_path,
                    "w",
                    compression=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                ) as target_archive:
                    for member in source_archive.infolist():
                        member_info = zipfile.ZipInfo(member.filename, member.date_time)
                        member_info.comment = member.comment
                        member_info.create_system = member.create_system
                        member_info.create_version = member.create_version
                        member_info.extract_version = member.extract_version
                        member_info.flag_bits = member.flag_bits
                        member_info.volume = member.volume
                        member_info.internal_attr = member.internal_attr
                        member_info.external_attr = member.external_attr

                        if member.is_dir():
                            target_archive.writestr(member_info, b"")
                            continue

                        target_archive.writestr(
                            member_info,
                            source_archive.read(member.filename),
                            compress_type=zipfile.ZIP_DEFLATED,
                            compresslevel=9,
                        )
        except zipfile.BadZipFile as exc:
            raise ConversionError(f"Failed to read office document archive: {exc}") from exc
        except Exception as exc:
            raise ConversionError(f"Document compression failed: {exc}") from exc

        if not output_path.exists():
            raise ConversionError("Compressed file was not created.")

        original_kb = input_path.stat().st_size / 1024
        compressed_kb = output_path.stat().st_size / 1024
        saved_pct = 100 * (1 - compressed_kb / original_kb) if original_kb else 0
        logger.info(
            "Repack complete: %.1f KB → %.1f KB (%.1f%% saved)",
            original_kb,
            compressed_kb,
            saved_pct,
        )

        return output_path

    def compress(self, input_path: Path, quality: str = "medium") -> Path:
        """
        Compress *input_path* and write the result to ``output_dir``.

        Supported same-format compression targets:
        - PDF  → optimised PDF
        - DOCX → repacked DOCX
        - PPTX → repacked PPTX
        """
        if not input_path.exists():
            raise InvalidFileError(f"File not found: {input_path.name}")

        extension = get_file_extension(input_path.name)

        if extension == "pdf":
            return self._compress_pdf(input_path, quality)

        if extension in {"docx", "pptx"}:
            return self._compress_office_archive(input_path)

        raise InvalidFileError(
            "Compression preserves original format only for PDF, DOCX, and PPTX files."
        )
