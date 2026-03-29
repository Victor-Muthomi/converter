"""
DOCX → PDF converter.

Uses LibreOffice in *headless* mode via ``subprocess``.  LibreOffice must
be installed on the host (``libreoffice`` on Linux).
"""

import logging
import subprocess
from pathlib import Path

from app.converters.base import BaseConverter
from app.utils.exceptions import ConversionError
from app.utils.helpers import find_system_tool

logger = logging.getLogger(__name__)

# ── LibreOffice binary resolution ──────────────────────────────────────────
# Centralised here so it is easy to extend with macOS / Windows paths later.
_LIBREOFFICE_CANDIDATES = [
    "libreoffice",          # most Linux distros
    "soffice",              # alternative symlink
    "/usr/bin/libreoffice",
]


class DocxToPdfConverter(BaseConverter):
    """Convert DOCX documents to PDF using LibreOffice headless."""

    input_format = "docx"
    output_format = "pdf"

    def convert(self, input_file: str, output_file: str) -> str:
        """
        Run LibreOffice headless to convert *input_file* (DOCX) to PDF.

        LibreOffice writes the output to the same directory as the input
        with the ``.pdf`` extension, so we move it to *output_file* afterwards.
        """
        input_path = Path(input_file)
        output_path = Path(output_file)
        lo_binary = find_system_tool(
            "LibreOffice",
            _LIBREOFFICE_CANDIDATES,
            install_hint="sudo apt-get install libreoffice",
        )

        logger.info("Converting %s → PDF via LibreOffice", input_path.name)

        try:
            subprocess.run(
                [
                    lo_binary,
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", str(output_path.parent),
                    str(input_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            logger.error("LibreOffice conversion failed: %s", exc.stderr)
            raise ConversionError(
                f"LibreOffice failed to convert '{input_path.name}': {exc.stderr}"
            ) from exc

        # LibreOffice names the output after the input stem
        lo_output = output_path.parent / f"{input_path.stem}.pdf"

        if not lo_output.exists():
            raise ConversionError(
                f"Expected output file '{lo_output}' was not created by LibreOffice."
            )

        # Move to the requested output path if it differs
        if lo_output != output_path:
            lo_output.rename(output_path)

        logger.info("Conversion complete → %s", output_path.name)
        return str(output_path)
