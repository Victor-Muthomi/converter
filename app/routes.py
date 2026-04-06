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
from app.services.merger import DocumentMerger
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
    Accept one or more file uploads and a ``target_format`` field, convert
    the files, and return the result as a downloadable attachment.

    Form fields:
        file:          One or more documents to convert (multipart file).
        target_format: Desired output extension, e.g. ``pdf``, ``docx``.
    """
    engine: ConversionEngine = current_app.config["CONVERSION_ENGINE"]
    file_mgr: FileManager = current_app.config["FILE_MANAGER"]
    upload_dir: Path = current_app.config["UPLOAD_FOLDER"]
    output_dir: Path = current_app.config["OUTPUT_FOLDER"]

    try:
        # 1. Validate target format parameter
        target_format = request.form.get("target_format", "").strip().lower()
        if not target_format:
            raise InvalidFileError(
                "Missing required form field: 'target_format'."
            )

        # 2. Validate and save uploaded files
        uploaded_files = request.files.getlist("file")
        file_mgr.validate_uploads(uploaded_files)
        saved_paths = file_mgr.save_uploads(uploaded_files, upload_dir)

        # 3. Run conversion(s)
        result_paths = [
            Path(engine.run(str(saved_path), target_format))
            for saved_path in saved_paths
        ]

        # 4. Return the converted file or a ZIP bundle for batches
        if len(result_paths) == 1:
            return send_file(
                result_paths[0],
                as_attachment=True,
                download_name=result_paths[0].name,
            )

        archive_path = file_mgr.create_archive(
            result_paths,
            output_dir,
            archive_name=f"docforge_batch_{target_format}.zip",
        )
        return send_file(
            archive_path,
            as_attachment=True,
            download_name=f"docforge_batch_{target_format}.zip",
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


@api.route("/merge", methods=["POST"])
def merge_documents():
    """
    Accept multiple uploaded documents, convert them to PDF when needed,
    and return a single merged PDF in upload order.
    """
    file_mgr: FileManager = current_app.config["FILE_MANAGER"]
    merger: DocumentMerger = current_app.config["DOCUMENT_MERGER"]
    upload_dir: Path = current_app.config["UPLOAD_FOLDER"]

    try:
        uploaded_files = request.files.getlist("file")
        file_mgr.validate_uploads(uploaded_files)

        if len(uploaded_files) < 2:
            raise InvalidFileError("Merge requires at least two files.")

        saved_paths = file_mgr.save_uploads(uploaded_files, upload_dir)
        merged_path = merger.merge(saved_paths)

        return send_file(
            merged_path,
            as_attachment=True,
            download_name="docforge_merged.pdf",
        )

    except (InvalidFileError, UnsupportedConversionError) as exc:
        logger.warning("Client error: %s", exc.message)
        return jsonify({"error": exc.message}), 400

    except ConversionError as exc:
        logger.error("Merge error: %s", exc.message)
        return jsonify({"error": exc.message}), 500

    except DocForgeError as exc:
        logger.error("DocForge error: %s", exc.message)
        return jsonify({"error": exc.message}), 500

    except Exception:
        logger.exception("Unexpected error in /merge")
        return jsonify({"error": "An unexpected server error occurred."}), 500
