# DocForge

A modular document conversion API built with Flask.

## Supported Conversions

| Input  | Output | Engine              |
|--------|--------|---------------------|
| DOCX   | HTML   | Pandoc              |
| DOCX   | MD     | Pandoc              |
| DOCX   | PDF    | LibreOffice headless|
| HTML   | MD     | Pandoc              |
| MD     | PDF    | Pandoc + WeasyPrint |
| PDF    | DOC    | pdf2docx + LibreOffice |
| PDF    | DOCX   | pdf2docx            |
| PDF    | HTML   | PyMuPDF             |
| PDF    | MD     | PyMuPDF4LLM         |
| HTML   | PDF    | WeasyPrint          |
| TXT    | PDF    | WeasyPrint          |

## System Requirements

- **Python** 3.11+
- **LibreOffice** (for DOCX → PDF conversion)
- **Pandoc** (for DOCX → Markdown conversion)
- **Pandoc** is also required for Markdown → PDF because Markdown is first
  rendered to standalone HTML before PDF generation.
- **LibreOffice** is also required for PDF → DOC because the final DOC export
  is performed from an intermediate DOCX file.

```bash
# Ubuntu / Debian
sudo apt-get install libreoffice
sudo apt-get install pandoc

# WeasyPrint system dependencies
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libcairo2
```

DocForge validates required external tools at conversion time and returns a
clear error if a dependency such as Pandoc or LibreOffice is missing.

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install Python dependencies
pip install -r requirements.txt
```

## Running Locally

```bash
python run.py
```

The server starts on **http://127.0.0.1:5002**.

## API Endpoints

### Health Check

```
GET /health
```

```bash
curl http://127.0.0.1:5002/health
```

Response:
```json
{"service": "docforge", "status": "healthy"}
```

### Convert a File

```
POST /convert
```

| Field          | Type | Description                          |
|----------------|------|--------------------------------------|
| `file`         | file | The document to convert              |
| `target_format`| text | Desired output extension (e.g. `pdf`)|

#### DOCX → PDF

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@document.docx" \
  -F "target_format=pdf" \
  -o converted.pdf
```

#### DOCX → Markdown

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@document.docx" \
  -F "target_format=md" \
  -o converted.md
```

#### DOCX → HTML

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@document.docx" \
  -F "target_format=html" \
  -o converted.html
```

#### HTML → Markdown

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@page.html" \
  -F "target_format=md" \
  -o converted.md
```

#### Markdown → PDF

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@document.md" \
  -F "target_format=pdf" \
  -o converted.pdf
```

#### PDF → DOCX

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@document.pdf" \
  -F "target_format=docx" \
  -o converted.docx
```

#### PDF → DOC

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@document.pdf" \
  -F "target_format=doc" \
  -o converted.doc
```

#### PDF → HTML

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@document.pdf" \
  -F "target_format=html" \
  -o converted.html
```

#### HTML → PDF

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@page.html" \
  -F "target_format=pdf" \
  -o converted.pdf
```

#### PDF → Markdown

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@document.pdf" \
  -F "target_format=md" \
  -o converted.md
```

#### TXT → PDF

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@notes.txt" \
  -F "target_format=pdf" \
  -o converted.pdf
```

## Project Structure

```
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Configuration
│   ├── routes.py            # Flask API routes
│   ├── converters/
│   │   ├── base.py          # Abstract base converter
│   │   ├── docx_to_html.py  # Pandoc converter
│   │   ├── docx_to_md.py    # Pandoc converter
│   │   ├── docx_to_pdf.py   # LibreOffice converter
│   │   ├── html_to_md.py    # Pandoc converter
│   │   ├── md_to_pdf.py     # Pandoc + WeasyPrint converter
│   │   ├── pdf_to_doc.py    # pdf2docx + LibreOffice converter
│   │   ├── pdf_to_docx.py   # pdf2docx converter
│   │   ├── pdf_to_html.py   # PyMuPDF converter
│   │   ├── pdf_to_md.py     # PyMuPDF4LLM converter
│   │   ├── html_to_pdf.py   # WeasyPrint converter
│   │   └── txt_to_pdf.py    # WeasyPrint converter
│   ├── services/
│   │   ├── registry.py      # Converter registry
│   │   ├── engine.py        # Conversion orchestration
│   │   └── file_manager.py  # Upload handling
│   └── utils/
│       ├── exceptions.py    # Custom exceptions
│       └── helpers.py       # Filename utilities
├── run.py                   # Dev server entry point
├── requirements.txt
└── README.md
```

## Adding a New Converter

1. Create `app/converters/my_format_to_other.py`
2. Subclass `BaseConverter`, set `input_format` and `output_format`
3. Implement the `convert()` method
4. Register it in `app/__init__.py`:
   ```python
   registry.register(MyFormatToOtherConverter())
   ```
5. Add the input extension to `ALLOWED_INPUT_EXTENSIONS` in `config.py`

## Notes on PDF → DOC

PDF → DOC uses an intermediate DOCX file under the hood. This keeps the
implementation compatible with the existing converter architecture and is
generally more stable than attempting direct PDF → DOC export. Legacy DOC
output may still lose some layout fidelity compared with DOCX, depending on
the source PDF.

## Notes on DOCX → Markdown

DOCX → Markdown uses Pandoc to produce GitHub-Flavored Markdown. Rich Word
features that do not map cleanly to Markdown may be simplified during export,
which keeps the output practical for plain-text workflows.

## Notes on DOCX → HTML

DOCX → HTML uses Pandoc to produce standalone HTML. The output is convenient
for browser viewing and downstream HTML-based conversions, though Word-specific
layout or styling may be simplified during export.

## Notes on HTML → Markdown

HTML → Markdown uses Pandoc to produce GitHub-Flavored Markdown. Complex HTML
structures or raw embedded elements may be simplified during export so the
result stays practical for Markdown-based workflows.

## Notes on Markdown → PDF

Markdown → PDF uses Pandoc plus WeasyPrint through an intermediate standalone
HTML file. This keeps PDF generation reliable without requiring a LaTeX engine,
though the final appearance will follow HTML/CSS rendering rather than a
Word-processor layout model.

## Notes on PDF → HTML

PDF → HTML is extracted page-by-page with PyMuPDF and combined into a single
HTML document. The output is suitable for inspection and downstream HTML-based
processing, but complex PDFs may still produce positioned markup that reflects
the original page layout rather than semantic HTML.

## Notes on TXT → PDF

TXT → PDF renders plain text through a simple HTML template using WeasyPrint.
Common text encodings are attempted automatically, and the output preserves
line breaks and spacing in a print-friendly monospace layout.

## License

MIT
