"""
Abstract base class for all DocForge converters.

Every converter **must** subclass ``BaseConverter`` and implement
the ``convert`` method.  The ``input_format`` / ``output_format``
attributes are used by the registry to look up the right converter
at runtime.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseConverter(ABC):
    """
    Contract that every converter must satisfy.

    Attributes:
        input_format:  Lowercase extension the converter reads  (e.g. "docx").
        output_format: Lowercase extension the converter writes (e.g. "pdf").
    """

    input_format: str = ""
    output_format: str = ""

    @abstractmethod
    def convert(self, input_file: str, output_file: str) -> str:
        """
        Convert *input_file* and write the result to *output_file*.

        Args:
            input_file:  Absolute path to the source file.
            output_file: Absolute path where the converted file should be saved.

        Returns:
            The absolute path to the converted file (usually *output_file*).

        Raises:
            ConversionError: If the conversion process fails.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.input_format}→{self.output_format}>"
