"""
DOCX → HTML converter.

Uses Pandoc via ``subprocess`` to convert Word documents into HTML.
Pandoc must be installed on the host and available on ``PATH``.
"""

import logging
import shutil
import subprocess
from pathlib import Path

from app.converters.base import BaseConverter
from app.utils.exceptions import ConversionError, ToolNotAvailableError

logger = logging.getLogger(__name__)

_PANDOC_CANDIDATES = [
    "pandoc",
    "/usr/bin/pandoc",
]


def _find_pandoc() -> str:
    """Return the first available Pandoc binary path, or raise."""
    for candidate in _PANDOC_CANDIDATES:
        if shutil.which(candidate):
            return candidate
    raise ToolNotAvailableError("Pandoc")


class DocxToHtmlConverter(BaseConverter):
    """Convert DOCX documents to HTML using Pandoc."""

    input_format = "docx"
    output_format = "html"

    def convert(self, input_file: str, output_file: str) -> str:
        """
        Run Pandoc to convert *input_file* (DOCX) into standalone HTML.

        Standalone HTML is used so the result is a complete document that can
        be opened directly in a browser or reused by later HTML-based converters.
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        pandoc_binary = _find_pandoc()

        logger.info("Converting %s → HTML via Pandoc", input_path.name)

        try:
            subprocess.run(
                [
                    pandoc_binary,
                    "--from", "docx",
                    "--to", "html",
                    "--standalone",
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
                f"Pandoc failed to convert '{input_path.name}' to HTML: "
                f"{error_details}"
            ) from exc

        if not output_path.exists():
            raise ConversionError(
                f"Expected output file '{output_path}' was not created by Pandoc."
            )

        logger.info("Conversion complete → %s", output_path.name)
        return str(output_path)
