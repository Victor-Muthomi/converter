"""
Conversion engine.

Orchestrates the full conversion pipeline:
  1. Detect the input format from the file extension.
  2. Look up the correct converter in the registry.
  3. Build a safe output filename.
  4. Execute the conversion.
  5. Return the path to the converted file.

This keeps all conversion orchestration logic in one place, completely
separated from Flask routes and from the converters themselves.
"""

import logging
from pathlib import Path

from app.services.registry import ConverterRegistry
from app.utils.exceptions import ConversionError, DocForgeError, InvalidFileError
from app.utils.helpers import build_output_filename, get_file_extension

logger = logging.getLogger(__name__)


class ConversionEngine:
    """
    High-level entry point for performing conversions.

    Usage::

        engine = ConversionEngine(registry, output_dir=Path("/outputs"))
        result_path = engine.run("/uploads/report.docx", "pdf")
    """

    def __init__(self, registry: ConverterRegistry, output_dir: Path) -> None:
        """
        Args:
            registry:   Populated ``ConverterRegistry``.
            output_dir: Directory where converted files will be written.
        """
        self.registry = registry
        self.output_dir = output_dir

    def run(self, input_file: str, target_format: str) -> str:
        """
        Execute a conversion.

        Args:
            input_file:    Absolute path to the uploaded source file.
            target_format: Desired output extension (e.g. "pdf", "docx").

        Returns:
            Absolute path to the converted output file.

        Raises:
            InvalidFileError:          If *input_file* does not exist.
            UnsupportedConversionError: If no converter matches.
            ConversionError:           If the converter itself fails.
        """
        input_path = Path(input_file)

        # ── 1. Validate input ──────────────────────────────────────────────
        if not input_path.exists():
            raise InvalidFileError(f"Input file not found: {input_path}")

        # ── 2. Detect input format ─────────────────────────────────────────
        input_format = get_file_extension(input_path.name)
        target_format = target_format.lower().strip()

        logger.info(
            "Conversion requested: %s (%s → %s)",
            input_path.name, input_format, target_format,
        )

        # ── 3. Look up converter ──────────────────────────────────────────
        converter = self.registry.get(input_format, target_format)

        # ── 4. Build output path ──────────────────────────────────────────
        out_name = build_output_filename(input_path.name, target_format)
        output_path = self.output_dir / out_name

        # ── 5. Execute ────────────────────────────────────────────────────
        try:
            result = converter.convert(str(input_path), str(output_path))
        except DocForgeError:
            raise  # already a domain exception
        except Exception as exc:
            logger.exception("Unexpected error during conversion")
            raise ConversionError(
                f"Unexpected error converting '{input_path.name}': {exc}"
            ) from exc

        logger.info("Conversion succeeded → %s", result)
        return result
