"""
TXT → PDF converter.

Uses ``WeasyPrint`` to render plain text as a simple HTML document and
produce a PDF.  The source text is decoded conservatively using a small
set of common encodings so uploads from different environments are
handled more gracefully.
"""

import html
import logging
from pathlib import Path

from app.converters.base import BaseConverter
from app.utils.exceptions import ConversionError

logger = logging.getLogger(__name__)

_TEXT_ENCODINGS = [
    "utf-8-sig",
    "utf-16",
    "utf-16-le",
    "utf-16-be",
    "cp1252",
    "latin-1",
]


def _read_text_file(path: Path) -> str:
    """Read *path* using a small set of common text encodings."""
    raw = path.read_bytes()

    for encoding in _TEXT_ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise ConversionError(
        f"Could not decode '{path.name}' as text. "
        "Supported encodings include UTF-8, UTF-16, and common ANSI text."
    )


class TxtToPdfConverter(BaseConverter):
    """Convert plain text documents to PDF using WeasyPrint."""

    input_format = "txt"
    output_format = "pdf"

    def convert(self, input_file: str, output_file: str) -> str:
        """
        Render *input_file* (TXT) to a PDF at *output_file*.

        The text is escaped into a simple standalone HTML template so line
        breaks and spacing are preserved safely in the generated PDF.
        """
        input_path = Path(input_file)
        output_path = Path(output_file)

        logger.info("Converting %s → PDF via WeasyPrint", input_path.name)

        try:
            from weasyprint import HTML

            text_content = _read_text_file(input_path)
            html_document = (
                "<!DOCTYPE html>\n"
                '<html lang="en">\n'
                "<head>\n"
                '  <meta charset="utf-8">\n'
                f"  <title>{html.escape(input_path.stem)}</title>\n"
                "  <style>\n"
                "    @page { margin: 20mm; }\n"
                "    body {\n"
                "      font-family: 'Courier New', Courier, monospace;\n"
                "      font-size: 12pt;\n"
                "      line-height: 1.5;\n"
                "      color: #111827;\n"
                "      white-space: pre-wrap;\n"
                "      word-break: break-word;\n"
                "    }\n"
                "    pre {\n"
                "      margin: 0;\n"
                "      white-space: pre-wrap;\n"
                "      word-break: break-word;\n"
                "    }\n"
                "  </style>\n"
                "</head>\n"
                "<body>\n"
                f"<pre>{html.escape(text_content)}</pre>\n"
                "</body>\n"
                "</html>\n"
            )
            HTML(string=html_document, base_url=str(input_path.parent)).write_pdf(str(output_path))
        except ImportError as exc:
            raise ConversionError(
                "The 'weasyprint' package is not installed. "
                "Run: pip install weasyprint"
            ) from exc
        except ConversionError:
            raise
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
