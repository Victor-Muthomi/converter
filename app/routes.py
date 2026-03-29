"""
Flask routes for DocForge.

All HTTP-facing logic lives here.  Business logic is delegated to the
``ConversionEngine`` and ``FileManager`` services — routes only handle
request parsing, response formatting, and error translation.
"""

import logging
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_file

from app.services.engine import ConversionEngine
from app.services.file_manager import FileManager
from app.utils.exceptions import (
    ConversionError,
    DocForgeError,
    InvalidFileError,
    UnsupportedConversionError,
)

logger = logging.getLogger(__name__)

api = Blueprint("api", __name__)


# ── Health check ────────────────────────────────────────────────────────────

@api.route("/health", methods=["GET"])
def health():
    """Return a simple JSON health-check response."""
    return jsonify({"status": "healthy", "service": "docforge"}), 200


# ── Conversion endpoint ────────────────────────────────────────────────────

@api.route("/convert", methods=["POST"])
def convert():
    """
    Accept a file upload and a ``target_format`` field, convert the file,
    and return the result as a downloadable attachment.

    Form fields:
        file:          The document to convert (multipart file).
        target_format: Desired output extension, e.g. ``pdf``, ``docx``.
    """
    engine: ConversionEngine = current_app.config["CONVERSION_ENGINE"]
    file_mgr: FileManager = current_app.config["FILE_MANAGER"]
    upload_dir: Path = current_app.config["UPLOAD_FOLDER"]

    try:
        # 1. Validate target format parameter
        target_format = request.form.get("target_format", "").strip().lower()
        if not target_format:
            raise InvalidFileError(
                "Missing required form field: 'target_format'."
            )

        # 2. Validate and save uploaded file
        uploaded = request.files.get("file")
        file_mgr.validate_upload(uploaded)
        saved_path = file_mgr.save_upload(uploaded, upload_dir)

        # 3. Run conversion
        result_path = engine.run(str(saved_path), target_format)

        # 4. Return converted file
        return send_file(
            result_path,
            as_attachment=True,
            download_name=Path(result_path).name,
        )

    except (InvalidFileError, UnsupportedConversionError) as exc:
        logger.warning("Client error: %s", exc.message)
        return jsonify({"error": exc.message}), 400

    except ConversionError as exc:
        logger.error("Conversion error: %s", exc.message)
        return jsonify({"error": exc.message}), 500

    except DocForgeError as exc:
        logger.error("DocForge error: %s", exc.message)
        return jsonify({"error": exc.message}), 500

    except Exception as exc:
        logger.exception("Unexpected error in /convert")
        return jsonify({"error": "An unexpected server error occurred."}), 500
