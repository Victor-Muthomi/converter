"""
EPUB -> PDF converter.

Uses a two-step conversion pipeline:
  1. Pandoc converts EPUB into a standalone HTML document.
  2. WeasyPrint renders that HTML into PDF.
"""

import logging
import subprocess
from pathlib import Path

from app.converters.base import BaseConverter
from app.services.file_manager import FileManager
from app.utils.exceptions import ConversionError
from app.utils.helpers import find_system_tool

logger = logging.getLogger(__name__)

_PANDOC_CANDIDATES = [
    "pandoc",
    "/usr/bin/pandoc",
]


class EpubToPdfConverter(BaseConverter):
    """Convert EPUB documents to PDF using Pandoc and WeasyPrint."""

    input_format = "epub"
    output_format = "pdf"

    def convert(self, input_file: str, output_file: str) -> str:
        """
        Convert *input_file* (EPUB) to *output_file* (PDF).
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        pandoc_binary = find_system_tool(
            "Pandoc",
            _PANDOC_CANDIDATES,
            install_hint="sudo apt-get install pandoc",
        )
        temp_dir = FileManager.create_temp_dir(prefix="docforge_epub_to_pdf_")
        intermediate_html = temp_dir / f"{input_path.stem}.html"

        logger.info("Converting %s -> PDF via Pandoc + WeasyPrint", input_path.name)

        try:
            try:
                subprocess.run(
                    [
                        pandoc_binary,
                        "--from", "epub",
                        "--to", "html",
                        "--standalone",
                        "--output", str(intermediate_html),
                        str(input_path),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                error_details = exc.stderr.strip() or exc.stdout.strip() or str(exc)
                logger.error("Pandoc conversion failed: %s", error_details)
                raise ConversionError(
                    f"Pandoc failed to convert '{input_path.name}' to HTML: "
                    f"{error_details}"
                ) from exc

            if not intermediate_html.exists():
                raise ConversionError(
                    f"Expected intermediate file '{intermediate_html}' was not created."
                )

            try:
                from weasyprint import HTML

                HTML(filename=str(intermediate_html)).write_pdf(str(output_path))
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
        finally:
            FileManager.cleanup(temp_dir)

        if not output_path.exists():
            raise ConversionError(
                f"Expected output file '{output_path}' was not created."
            )

        logger.info("Conversion complete -> %s", output_path.name)
        return str(output_path)
