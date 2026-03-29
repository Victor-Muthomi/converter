"""
PDF → DOCX converter.

Uses the ``pdf2docx`` library to extract content from a PDF and
reconstruct it as a DOCX document.
"""

import logging
from pathlib import Path

from app.converters.base import BaseConverter
from app.utils.exceptions import ConversionError

logger = logging.getLogger(__name__)


class PdfToDocxConverter(BaseConverter):
    """Convert PDF documents to DOCX using pdf2docx."""

    input_format = "pdf"
    output_format = "docx"

    def convert(self, input_file: str, output_file: str) -> str:
        """
        Parse *input_file* (PDF) and write a DOCX to *output_file*.

        The ``pdf2docx.Converter`` is used as a context manager to
        guarantee that internal resources are released even on failure.
        """
        input_path = Path(input_file)
        output_path = Path(output_file)

        logger.info("Converting %s → DOCX via pdf2docx", input_path.name)

        try:
            # Import here so the module can be loaded even if pdf2docx
            # is not installed (useful for registry introspection).
            from pdf2docx import Converter as Pdf2DocxConverter

            converter = Pdf2DocxConverter(str(input_path))
            try:
                converter.convert(str(output_path))
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

        if not output_path.exists():
            raise ConversionError(
                f"Expected output file '{output_path}' was not created."
            )

        logger.info("Conversion complete → %s", output_path.name)
        return str(output_path)
