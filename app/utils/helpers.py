"""
DocForge helper utilities.

Small, stateless functions used across multiple modules.
"""

import shutil
import uuid
from pathlib import Path

from app.utils.exceptions import ToolNotAvailableError
from werkzeug.utils import secure_filename


def get_file_extension(filename: str) -> str:
    """
    Extract the lowercase file extension without the leading dot.

    Args:
        filename: Original filename (e.g. "report.DOCX").

    Returns:
        Lowercase extension string (e.g. "docx").
    """
    return Path(filename).suffix.lstrip(".").lower()


def generate_safe_filename(original_filename: str) -> str:
    """
    Produce a collision-free filename while preserving the original extension.

    Uses ``werkzeug.secure_filename`` plus a UUID4 prefix so that two users
    uploading ``report.docx`` at the same time never overwrite each other.

    Args:
        original_filename: The raw filename from the upload.

    Returns:
        A sanitised, unique filename.
    """
    safe_name = secure_filename(original_filename)
    stem = Path(safe_name).stem
    ext = Path(safe_name).suffix
    unique_name = f"{uuid.uuid4().hex[:12]}_{stem}{ext}"
    return unique_name


def build_output_filename(input_filename: str, target_format: str) -> str:
    """
    Replace the extension of *input_filename* with *target_format*.

    Args:
        input_filename: Current filename (e.g. "abc123_report.docx").
        target_format:  Desired output format without dot (e.g. "pdf").

    Returns:
        New filename with the target extension (e.g. "abc123_report.pdf").
    """
    stem = Path(input_filename).stem
    return f"{stem}.{target_format}"


def find_system_tool(
    tool_name: str,
    candidates: list[str],
    install_hint: str | None = None,
) -> str:
    """
    Return the first available executable for *tool_name*.

    Args:
        tool_name: Friendly tool name shown in error messages.
        candidates: Executable names or absolute paths to try with ``which``.
        install_hint: Optional user-facing installation hint.

    Raises:
        ToolNotAvailableError: If none of the candidates can be resolved.
    """
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    raise ToolNotAvailableError(tool_name, install_hint=install_hint)
