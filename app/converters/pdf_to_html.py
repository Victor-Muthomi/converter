"""
PDF → HTML converter.

Uses ``PyMuPDF`` to extract each PDF page as HTML and combines the page
fragments into a single HTML document.
"""

import logging
from pathlib import Path

from app.converters.base import BaseConverter
from app.utils.exceptions import ConversionError

logger = logging.getLogger(__name__)


def _strip_html_wrapper(html: str) -> str:
    """
    Remove document-level wrappers returned by page-level HTML extraction.

    ``Page.get_text("html")`` may include ``<html>`` / ``<body>`` tags per
    page, which would otherwise produce invalid nested markup when multiple
    pages are combined into one output document.
    """
    lowered = html.lower()
    body_start = lowered.find("<body")
    if body_start != -1:
        start = html.find(">", body_start)
        if start != -1:
            html = html[start + 1:]

    body_end = html.lower().rfind("</body>")
    if body_end != -1:
        html = html[:body_end]

    return html.strip()


class PdfToHtmlConverter(BaseConverter):
    """Convert PDF documents to HTML using PyMuPDF."""

    input_format = "pdf"
    output_format = "html"

    def convert(self, input_file: str, output_file: str) -> str:
        """
        Extract HTML from *input_file* (PDF) and write it to *output_file*.

        Each page is rendered to HTML individually and wrapped in a simple
        document shell so the output remains a single valid HTML file.
        """
        input_path = Path(input_file)
        output_path = Path(output_file)

        logger.info("Converting %s → HTML via PyMuPDF", input_path.name)

        try:
            # Lazy import keeps registry/module imports working even when the
            # optional PDF-to-HTML dependency is not installed.
            import pymupdf
        except ImportError:
            try:
                import fitz as pymupdf
            except ImportError as exc:
                raise ConversionError(
                    "The 'PyMuPDF' package is not installed. "
                    "Run: pip install PyMuPDF"
                ) from exc

        try:
            with pymupdf.open(str(input_path)) as document:
                page_fragments: list[str] = []

                for index, page in enumerate(document):
                    page_html = _strip_html_wrapper(page.get_text("html"))
                    page_fragments.append(
                        f'<section class="pdf-page" data-page="{index + 1}">\n'
                        f"{page_html}\n"
                        "</section>"
                    )

            html_output = (
                "<!DOCTYPE html>\n"
                '<html lang="en">\n'
                "<head>\n"
                '  <meta charset="utf-8">\n'
                f"  <title>{input_path.stem}</title>\n"
                "  <style>\n"
                "    body { margin: 0; padding: 24px; background: #f5f5f5; }\n"
                "    .pdf-page { margin: 0 auto 24px; background: #fff; }\n"
                "  </style>\n"
                "</head>\n"
                "<body>\n"
                f"{chr(10).join(page_fragments)}\n"
                "</body>\n"
                "</html>\n"
            )
            output_path.write_text(html_output, encoding="utf-8")
        except ConversionError:
            raise
        except Exception as exc:
            logger.error("PyMuPDF conversion failed: %s", exc)
            raise ConversionError(
                f"Failed to convert '{input_path.name}' to HTML: {exc}"
            ) from exc

        if not output_path.exists():
            raise ConversionError(
                f"Expected output file '{output_path}' was not created."
            )

        logger.info("Conversion complete → %s", output_path.name)
        return str(output_path)
