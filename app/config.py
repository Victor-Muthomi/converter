"""
DocForge application configuration.

All path-based settings use ``pathlib.Path``.  Directories are created
automatically so the app can start cleanly on a fresh checkout.
"""

import os
from pathlib import Path


# ── Project root is the parent of the ``app/`` package ──────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Flask configuration values for DocForge."""

    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "docforge-dev-secret-change-me")

    # File handling
    UPLOAD_FOLDER: Path = BASE_DIR / "uploads"
    OUTPUT_FOLDER: Path = BASE_DIR / "outputs"
    MAX_CONTENT_LENGTH: int = 50 * 1024 * 1024  # 50 MB

    # Allowed input extensions (add more as converters are registered)
    ALLOWED_INPUT_EXTENSIONS: set[str] = {"docx", "pdf", "html", "md"}


# ── Ensure required directories exist ──────────────────────────────────────
Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
Config.OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
