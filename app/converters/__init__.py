"""
DocForge converters package.

Importing this module makes all concrete converter classes available
at the package level for convenient registration.
"""

from app.converters.base import BaseConverter
from app.converters.docx_to_html import DocxToHtmlConverter
from app.converters.docx_to_epub import DocxToEpubConverter
from app.converters.docx_to_md import DocxToMarkdownConverter
from app.converters.docx_to_pdf import DocxToPdfConverter
from app.converters.epub_to_html import EpubToHtmlConverter
from app.converters.epub_to_md import EpubToMarkdownConverter
from app.converters.epub_to_pdf import EpubToPdfConverter
from app.converters.html_to_epub import HtmlToEpubConverter
from app.converters.html_to_md import HtmlToMarkdownConverter
from app.converters.html_to_pdf import HtmlToPdfConverter
from app.converters.md_to_epub import MarkdownToEpubConverter
from app.converters.md_to_pdf import MarkdownToPdfConverter
from app.converters.pdf_to_doc import PdfToDocConverter
from app.converters.pdf_to_html import PdfToHtmlConverter
from app.converters.pdf_to_md import PdfToMarkdownConverter
from app.converters.pdf_to_docx import PdfToDocxConverter
from app.converters.pptx_to_pdf import PptxToPdfConverter
from app.converters.txt_to_epub import TxtToEpubConverter
from app.converters.txt_to_pdf import TxtToPdfConverter

__all__ = [
    "BaseConverter",
    "DocxToHtmlConverter",
    "DocxToEpubConverter",
    "DocxToMarkdownConverter",
    "DocxToPdfConverter",
    "EpubToHtmlConverter",
    "EpubToMarkdownConverter",
    "EpubToPdfConverter",
    "HtmlToEpubConverter",
    "HtmlToMarkdownConverter",
    "MarkdownToEpubConverter",
    "MarkdownToPdfConverter",
    "PdfToDocConverter",
    "PdfToHtmlConverter",
    "PdfToDocxConverter",
    "PdfToMarkdownConverter",
    "PptxToPdfConverter",
    "HtmlToPdfConverter",
    "TxtToEpubConverter",
    "TxtToPdfConverter",
]
