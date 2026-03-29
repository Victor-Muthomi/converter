"""
HTML → PDF converter.

Uses ``weasyprint`` to render a local HTML file and produce a PDF.
"""

import logging
from pathlib import Path

from app.converters.base import BaseConverter
from app.utils.exceptions import ConversionError

logger = logging.getLogger(__name__)


class HtmlToPdfConverter(BaseConverter):
    """Convert HTML documents to PDF using WeasyPrint."""

    input_format = "html"
    output_format = "pdf"

    def convert(self, input_file: str, output_file: str) -> str:
        """
        Render *input_file* (HTML) to a PDF at *output_file*.

        WeasyPrint supports CSS styling, embedded images (with local
        paths), and basic HTML5 — making it suitable for report/invoice
        generation.
        """
        input_path = Path(input_file)
        output_path = Path(output_file)

        logger.info("Converting %s → PDF via WeasyPrint", input_path.name)

        try:
            # Lazy import so the module loads even without weasyprint.
            from weasyprint import HTML

            HTML(filename=str(input_path)).write_pdf(str(output_path))

        except ImportError as exc:
            raise ConversionError(
                "The 'weasyprint' package is not installed. "
                "Run: pip install weasyprint"
            ) from exc
        except Exception as exc:
            logger.error("WeasyPrint conversion failed: %s", exc)
            raise ConversionError(
                f"Failed to convert '{input_path.name}' to PDF: {exc}"
            ) from exc

        if not output_path.exists():
            raise ConversionError(
                f"Expected output file '{output_path}' was not created."
            )

        logger.info("Conversion complete → %s", output_path.name)
        return str(output_path)
