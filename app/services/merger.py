"""
Document merge service.

Converts supported input files to PDF when necessary and combines them
into a single merged PDF in upload order.
"""

import logging
from pathlib import Path
from typing import Iterable

from app.services.engine import ConversionEngine
from app.utils.exceptions import ConversionError
from app.utils.helpers import generate_safe_filename, get_file_extension

logger = logging.getLogger(__name__)


class DocumentMerger:
    """Merge multiple supported documents into a single PDF."""

    def __init__(self, engine: ConversionEngine, output_dir: Path) -> None:
        self.engine = engine
        self.output_dir = output_dir

    def merge(self, input_files: Iterable[Path]) -> Path:
        """
        Merge input files into one PDF.

        Non-PDF inputs are converted to PDF first using the existing
        conversion engine so merge support stays aligned with the app's
        registered converters.
        """
        input_paths = list(input_files)
        if len(input_paths) < 2:
            raise ConversionError("At least two documents are required to merge.")

        pdf_paths = [self._ensure_pdf(path) for path in input_paths]
        output_path = self.output_dir / generate_safe_filename("docforge_merged.pdf")

        try:
            import fitz
        except ImportError as exc:
            raise ConversionError(
                "PyMuPDF is not installed. Run: pip install PyMuPDF"
            ) from exc

        logger.info("Merging %d documents into %s", len(pdf_paths), output_path.name)

        merged = fitz.open()
        try:
            for pdf_path in pdf_paths:
                with fitz.open(str(pdf_path)) as source_pdf:
                    merged.insert_pdf(source_pdf)

            merged.save(str(output_path))
        except Exception as exc:
            logger.error("PDF merge failed: %s", exc)
            raise ConversionError(f"Failed to merge documents: {exc}") from exc
        finally:
            merged.close()

        if not output_path.exists():
            raise ConversionError(
                f"Expected merged output file '{output_path}' was not created."
            )

        logger.info("Merge complete → %s", output_path.name)
        return output_path

    def _ensure_pdf(self, input_path: Path) -> Path:
        """Return a PDF path for the provided input file."""
        if get_file_extension(input_path.name) == "pdf":
            return input_path

        return Path(self.engine.run(str(input_path), "pdf"))
