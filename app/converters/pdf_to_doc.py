"""
PDF → DOC converter.

Uses a two-step conversion pipeline for better compatibility:
  1. ``pdf2docx`` converts the PDF into an intermediate DOCX file.
  2. LibreOffice headless converts that DOCX into legacy DOC format.

This approach is more reliable than trying to produce ``.doc`` directly
from PDF with a single tool, while still fitting the existing converter
architecture used throughout DocForge.
"""

import logging
import shutil
import subprocess
from pathlib import Path

from app.converters.base import BaseConverter
from app.services.file_manager import FileManager
from app.utils.exceptions import ConversionError, ToolNotAvailableError

logger = logging.getLogger(__name__)

_LIBREOFFICE_CANDIDATES = [
    "libreoffice",
    "soffice",
    "/usr/bin/libreoffice",
]


def _find_libreoffice() -> str:
    """Return the first available LibreOffice binary path, or raise."""
    for candidate in _LIBREOFFICE_CANDIDATES:
        if shutil.which(candidate):
            return candidate
    raise ToolNotAvailableError("LibreOffice")


class PdfToDocConverter(BaseConverter):
    """Convert PDF documents to DOC using pdf2docx and LibreOffice."""

    input_format = "pdf"
    output_format = "doc"

    def convert(self, input_file: str, output_file: str) -> str:
        """
        Convert *input_file* (PDF) to *output_file* (DOC).

        A temporary DOCX artefact is created during the process and
        cleaned up afterwards regardless of success or failure.
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        lo_binary = _find_libreoffice()
        temp_dir = FileManager.create_temp_dir(prefix="docforge_pdf_to_doc_")

        intermediate_docx = temp_dir / f"{input_path.stem}.docx"
        temp_doc_output = temp_dir / f"{input_path.stem}.doc"

        logger.info("Converting %s → DOC via pdf2docx + LibreOffice", input_path.name)

        try:
            try:
                from pdf2docx import Converter as Pdf2DocxConverter

                converter = Pdf2DocxConverter(str(input_path))
                try:
                    converter.convert(str(intermediate_docx))
                finally:
                    converter.close()
            except ImportError as exc:
                raise ConversionError(
                    "The 'pdf2docx' package is not installed. "
                    "Run: pip install pdf2docx"
                ) from exc
            except Exception as exc:
                logger.error("pdf2docx conversion failed: %s", exc)
                raise ConversionError(
                    f"Failed to convert '{input_path.name}' to DOCX: {exc}"
                ) from exc

            if not intermediate_docx.exists():
                raise ConversionError(
                    f"Expected intermediate file '{intermediate_docx}' was not created."
                )

            try:
                subprocess.run(
                    [
                        lo_binary,
                        "--headless",
                        "--convert-to", "doc",
                        "--outdir", str(temp_dir),
                        str(intermediate_docx),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                error_details = exc.stderr.strip() or exc.stdout.strip() or str(exc)
                logger.error("LibreOffice conversion failed: %s", error_details)
                raise ConversionError(
                    f"LibreOffice failed to convert '{intermediate_docx.name}' to DOC: "
                    f"{error_details}"
                ) from exc

            if not temp_doc_output.exists():
                raise ConversionError(
                    f"Expected output file '{temp_doc_output}' was not created by LibreOffice."
                )

            if output_path.exists():
                output_path.unlink()
            temp_doc_output.replace(output_path)

        finally:
            FileManager.cleanup(temp_dir)

        logger.info("Conversion complete → %s", output_path.name)
        return str(output_path)
