"""
DocForge converters package.

Importing this module makes all concrete converter classes available
at the package level for convenient registration.
"""

from app.converters.base import BaseConverter
from app.converters.docx_to_html import DocxToHtmlConverter
from app.converters.docx_to_md import DocxToMarkdownConverter
from app.converters.docx_to_pdf import DocxToPdfConverter
from app.converters.html_to_md import HtmlToMarkdownConverter
from app.converters.html_to_pdf import HtmlToPdfConverter
from app.converters.md_to_pdf import MarkdownToPdfConverter
from app.converters.pdf_to_doc import PdfToDocConverter
from app.converters.pdf_to_html import PdfToHtmlConverter
from app.converters.pdf_to_md import PdfToMarkdownConverter
from app.converters.pdf_to_docx import PdfToDocxConverter
from app.converters.txt_to_pdf import TxtToPdfConverter

__all__ = [
    "BaseConverter",
    "DocxToHtmlConverter",
    "DocxToMarkdownConverter",
    "DocxToPdfConverter",
    "HtmlToMarkdownConverter",
    "MarkdownToPdfConverter",
    "PdfToDocConverter",
    "PdfToHtmlConverter",
    "PdfToDocxConverter",
    "PdfToMarkdownConverter",
    "HtmlToPdfConverter",
    "TxtToPdfConverter",
]
