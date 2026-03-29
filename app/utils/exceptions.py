"""
DocForge custom exceptions.

Provides a hierarchy of domain-specific exceptions so that callers
(routes, CLI, etc.) can catch and translate errors into appropriate
user-facing messages without leaking implementation details.
"""


class DocForgeError(Exception):
    """Base exception for all DocForge errors."""

    def __init__(self, message: str = "An unexpected error occurred."):
        self.message = message
        super().__init__(self.message)


class ConversionError(DocForgeError):
    """Raised when a file conversion fails during processing."""

    def __init__(self, message: str = "File conversion failed."):
        super().__init__(message)


class UnsupportedConversionError(DocForgeError):
    """Raised when no converter is registered for the requested format pair."""

    def __init__(self, input_format: str, output_format: str):
        message = (
            f"Unsupported conversion: '{input_format}' → '{output_format}'. "
            f"No converter registered for this format pair."
        )
        super().__init__(message)


class InvalidFileError(DocForgeError):
    """Raised when an uploaded file is missing, empty, or has a disallowed extension."""

    def __init__(self, message: str = "The provided file is invalid."):
        super().__init__(message)


class ToolNotAvailableError(DocForgeError):
    """Raised when a required external tool (e.g. LibreOffice) is not installed."""

    def __init__(self, tool_name: str, install_hint: str | None = None):
        message = (
            f"Required system tool '{tool_name}' is not available on PATH. "
            f"Please install it before attempting this conversion."
        )
        if install_hint:
            message += f" Suggested install command: {install_hint}."
        super().__init__(message)
