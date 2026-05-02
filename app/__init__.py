"""
DocForge application factory.

``create_app()`` is the single entry point for creating a configured
Flask application.  It wires together configuration, logging, the
converter registry, and the route blueprint.
"""

import logging
import sys

from flask import Flask

from app.config import Config
from app.converters import (
    DocxToHtmlConverter,
    DocxToEpubConverter,
    DocxToMarkdownConverter,
    DocxToPdfConverter,
    EpubToDocxConverter,
    EpubToHtmlConverter,
    EpubToMarkdownConverter,
    EpubToPdfConverter,
    HtmlToEpubConverter,
    HtmlToMarkdownConverter,
    HtmlToPdfConverter,
    MarkdownToEpubConverter,
    MarkdownToPdfConverter,
    PdfToDocConverter,
    PdfToHtmlConverter,
    PdfToDocxConverter,
    PdfToMarkdownConverter,
    PptxToPdfConverter,
    TxtToEpubConverter,
    TxtToPdfConverter,
)
from app.routes import api
from app.web import web
from app.services.compressor import PdfCompressor
from app.services.engine import ConversionEngine
from app.services.file_manager import FileManager
from app.services.merger import DocumentMerger
from app.services.registry import ConverterRegistry


def _configure_logging() -> None:
    """Set up root logging with a readable console format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def create_app() -> Flask:
    """
    Application factory.

    Steps:
        1. Configure logging.
        2. Create the Flask instance & load config.
        3. Build and populate the converter registry.
        4. Instantiate services (engine, file manager).
        5. Register the API blueprint.

    Returns:
        A fully configured Flask application instance.
    """
    _configure_logging()
    logger = logging.getLogger(__name__)

    # ── Flask setup ────────────────────────────────────────────────────────
    app = Flask(__name__, static_folder="web/static", static_url_path="/static")
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
    app.config["UPLOAD_FOLDER"] = Config.UPLOAD_FOLDER
    app.config["OUTPUT_FOLDER"] = Config.OUTPUT_FOLDER

    # ── Converter registry ─────────────────────────────────────────────────
    registry = ConverterRegistry()
    registry.register(DocxToHtmlConverter())
    registry.register(DocxToEpubConverter())
    registry.register(DocxToMarkdownConverter())
    registry.register(DocxToPdfConverter())
    registry.register(EpubToDocxConverter())
    registry.register(EpubToHtmlConverter())
    registry.register(EpubToMarkdownConverter())
    registry.register(EpubToPdfConverter())
    registry.register(HtmlToEpubConverter())
    registry.register(HtmlToMarkdownConverter())
    registry.register(MarkdownToEpubConverter())
    registry.register(MarkdownToPdfConverter())
    registry.register(PdfToDocConverter())
    registry.register(PdfToHtmlConverter())
    registry.register(PdfToDocxConverter())
    registry.register(PdfToMarkdownConverter())
    registry.register(HtmlToPdfConverter())
    registry.register(PptxToPdfConverter())
    registry.register(TxtToEpubConverter())
    registry.register(TxtToPdfConverter())
    logger.info("Registered %d converter(s): %s", len(registry), registry.list_conversions())

    # ── Services ───────────────────────────────────────────────────────────
    file_manager = FileManager(allowed_extensions=Config.ALLOWED_INPUT_EXTENSIONS)
    engine = ConversionEngine(registry=registry, output_dir=Config.OUTPUT_FOLDER)
    merger = DocumentMerger(engine=engine, output_dir=Config.OUTPUT_FOLDER)
    compressor = PdfCompressor(output_dir=Config.OUTPUT_FOLDER, engine=engine)

    # Stash services on the app so routes can access them via current_app
    app.config["CONVERSION_ENGINE"] = engine
    app.config["FILE_MANAGER"] = file_manager
    app.config["DOCUMENT_MERGER"] = merger
    app.config["PDF_COMPRESSOR"] = compressor

    # ── Routes ─────────────────────────────────────────────────────────────
    app.register_blueprint(api)
    app.register_blueprint(web)

    logger.info("DocForge app initialised ✓")
    return app
