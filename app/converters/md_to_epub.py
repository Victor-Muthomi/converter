"""
Markdown -> EPUB converter.

Uses Pandoc via ``subprocess`` to convert Markdown documents into EPUB.
Pandoc must be installed on the host and available on ``PATH``.
"""

import logging
import subprocess
from pathlib import Path

from app.converters.base import BaseConverter
from app.utils.exceptions import ConversionError
from app.utils.helpers import find_system_tool

logger = logging.getLogger(__name__)

_PANDOC_CANDIDATES = [
    "pandoc",
    "/usr/bin/pandoc",
]


class MarkdownToEpubConverter(BaseConverter):
    """Convert Markdown documents to EPUB using Pandoc."""

    input_format = "md"
    output_format = "epub"

    def convert(self, input_file: str, output_file: str) -> str:
        """
        Run Pandoc to convert *input_file* (Markdown) into EPUB.
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        pandoc_binary = find_system_tool(
            "Pandoc",
            _PANDOC_CANDIDATES,
            install_hint="sudo apt-get install pandoc",
        )

        logger.info("Converting %s -> EPUB via Pandoc", input_path.name)

        try:
            subprocess.run(
                [
                    pandoc_binary,
                    "--from", "gfm",
                    "--to", "epub",
                    "--output", str(output_path),
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
                f"Pandoc failed to convert '{input_path.name}' to EPUB: "
                f"{error_details}"
            ) from exc

        if not output_path.exists():
            raise ConversionError(
                f"Expected output file '{output_path}' was not created by Pandoc."
            )

        logger.info("Conversion complete -> %s", output_path.name)
        return str(output_path)
