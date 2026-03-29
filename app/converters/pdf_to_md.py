"""
PDF → Markdown converter.

Uses ``pymupdf4llm`` to extract PDF content and render it as Markdown.
"""

import logging
from pathlib import Path

from app.converters.base import BaseConverter
from app.utils.exceptions import ConversionError

logger = logging.getLogger(__name__)


class PdfToMarkdownConverter(BaseConverter):
    """Convert PDF documents to Markdown using pymupdf4llm."""

    input_format = "pdf"
    output_format = "md"

    def convert(self, input_file: str, output_file: str) -> str:
        """
        Extract Markdown from *input_file* (PDF) and write it to
        *output_file* using UTF-8 encoding.
        """
        input_path = Path(input_file)
        output_path = Path(output_file)

        logger.info("Converting %s → Markdown via pymupdf4llm", input_path.name)

        try:
            # Import lazily so the module can still be imported even if the
            # optional Markdown extraction dependency is not installed.
            import pymupdf4llm

            markdown = pymupdf4llm.to_markdown(str(input_path))
            output_path.write_text(markdown, encoding="utf-8")
        except ImportError as exc:
            raise ConversionError(
                "The 'pymupdf4llm' package is not installed. "
                "Run: pip install pymupdf4llm"
            ) from exc
        except Exception as exc:
            logger.error("pymupdf4llm conversion failed: %s", exc)
            raise ConversionError(
                f"Failed to convert '{input_path.name}' to Markdown: {exc}"
            ) from exc

        if not output_path.exists():
            raise ConversionError(
                f"Expected output file '{output_path}' was not created."
            )

        logger.info("Conversion complete → %s", output_path.name)
        return str(output_path)
