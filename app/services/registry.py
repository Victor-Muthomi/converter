"""
Converter registry.

Provides a central look-up table that maps
``(input_format, output_format)`` pairs to concrete converter instances.
New converters are added with a single ``register()`` call.
"""

import logging
from typing import Optional

from app.converters.base import BaseConverter
from app.utils.exceptions import UnsupportedConversionError

logger = logging.getLogger(__name__)


class ConverterRegistry:
    """
    Thread-safe (for read-only use) registry of available converters.

    Usage::

        registry = ConverterRegistry()
        registry.register(DocxToPdfConverter())
        converter = registry.get("docx", "pdf")
    """

    def __init__(self) -> None:
        self._converters: dict[tuple[str, str], BaseConverter] = {}

    # ── public API ─────────────────────────────────────────────────────────

    def register(self, converter: BaseConverter) -> None:
        """
        Register a converter instance.

        The key is derived from the converter's ``input_format`` and
        ``output_format`` attributes so callers never have to specify
        them separately.
        """
        key = (converter.input_format.lower(), converter.output_format.lower())

        if key in self._converters:
            logger.warning("Overwriting existing converter for %s", key)

        self._converters[key] = converter
        logger.info("Registered converter: %s", converter)

    def get(self, input_format: str, output_format: str) -> BaseConverter:
        """
        Retrieve the converter for the given format pair.

        Raises:
            UnsupportedConversionError: If no converter is registered.
        """
        key = (input_format.lower(), output_format.lower())
        converter = self._converters.get(key)

        if converter is None:
            raise UnsupportedConversionError(input_format, output_format)

        return converter

    def list_conversions(self) -> list[tuple[str, str]]:
        """Return a sorted list of all registered ``(input, output)`` pairs."""
        return sorted(self._converters.keys())

    def __len__(self) -> int:
        return len(self._converters)

    def __repr__(self) -> str:
        return f"<ConverterRegistry conversions={len(self)}>"
