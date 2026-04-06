# DocForge

DocForge is a modular, privacy-conscious document conversion API built with
Flask for teams and individuals who need reliable file conversion without
depending on opaque third-party web tools.

## Why DocForge

Document conversion is a routine task, but many existing tools create
unnecessary friction. Online platforms often put basic features behind paywalls,
require sensitive files to be uploaded to third-party servers, provide little
clarity around file retention, and produce inconsistent output quality. They
also tend to solve only one narrow use case at a time, which makes them a poor
fit for repeatable business workflows and low-connectivity environments.

DocForge was created to offer a more practical alternative: a local-first,
extensible conversion system that gives users more privacy, control, and
transparency in how documents are processed. It is designed to support real
workflows across technical and non-technical use cases, whether the goal is to
convert a single file safely or integrate document processing into a larger
internal system.

## What It Delivers

- Privacy-first conversion for sensitive files
- Lower dependence on paid conversion platforms
- Support for multiple document workflows in one service
- Merge multiple documents into a single PDF
- Extensible architecture for adding new converters over time
- Better transparency for debugging and operational use
- A strong fit for self-hosted and internal business environments

## Who It Helps

- Developers building document processing pipelines
- Businesses handling internal reports and client files
- Students and administrators working across multiple formats
- Teams with confidentiality, compliance, or connectivity constraints

## Step 1: Check Python 3

Before setup, confirm that Python 3 is available on your system.

### macOS / Linux

```bash
python3 --version
```

### Windows

```powershell
py -3 --version
```

## Step 2: Install Python 3

### Install Python 3 on Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip
```

### Install Python 3 on Fedora

```bash
sudo dnf install -y python3 python3-pip
```

### Install Python 3 on RHEL / CentOS Stream

```bash
sudo dnf install -y python3 python3-pip
```

### Install Python 3 on Arch Linux

```bash
sudo pacman -Sy python python-pip
```

### Install Python 3 on macOS

```bash
brew install python
```

### Install Python 3 on Windows

Using `winget`:

```powershell
winget install -e --id Python.Python.3.11
```

Using `choco`:

```powershell
choco install python --yes
```

## Step 3: Install System Dependencies

DocForge requires **Python 3.11+** and a few external tools depending on the
conversion path you use:

- **LibreOffice** for DOCX → PDF, PPTX → PDF, and PDF → DOC
- **Pandoc** for DOCX → Markdown, HTML → Markdown, and Markdown → PDF
- **WeasyPrint system libraries** for HTML → PDF, Markdown → PDF, and TXT → PDF

### Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install -y libreoffice pandoc
sudo apt-get install -y libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libcairo2
```

DocForge validates required external tools at conversion time and returns a
clear error if a dependency such as Pandoc or LibreOffice is missing.

## Step 4: Set Up The Virtual Environment

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows PowerShell

```powershell
py -3 -m venv venv
.\venv\Scripts\Activate.ps1
```

## Step 5: Install Python Requirements

### macOS / Linux

```bash
python3 -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
py -3 -m pip install -r requirements.txt
```

## Step 6: Run The Program

### macOS / Linux

```bash
python3 run.py
```

### Windows

```powershell
py -3 run.py
```

The server starts on **http://127.0.0.1:5002**.

## Supported Conversions

| Input  | Output | Engine              |
|--------|--------|---------------------|
| DOCX   | HTML   | Pandoc              |
| DOCX   | MD     | Pandoc              |
| DOCX   | PDF    | LibreOffice headless|
| PPTX   | PDF    | LibreOffice headless|
| HTML   | MD     | Pandoc              |
| MD     | PDF    | Pandoc + WeasyPrint |
| PDF    | DOC    | pdf2docx + LibreOffice |
| PDF    | DOCX   | pdf2docx            |
| PDF    | HTML   | PyMuPDF             |
| PDF    | MD     | PyMuPDF4LLM         |
| HTML   | PDF    | WeasyPrint          |
| TXT    | PDF    | WeasyPrint          |

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
| `file`         | file | One or more documents to convert     |
| `target_format`| text | Desired output extension (e.g. `pdf`)|

If you upload a single file, DocForge returns the converted file directly.
If you upload multiple files with the same `target_format`, DocForge returns a
ZIP archive containing all converted outputs.

### Merge Documents Into One PDF

```
POST /merge
```

| Field  | Type | Description                                      |
|--------|------|--------------------------------------------------|
| `file` | file | Two or more supported documents to merge to PDF |

The merged PDF preserves the upload order from the request. Non-PDF inputs are
converted to PDF first using the existing conversion pipeline.

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

#### Batch conversion to PDF

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@chapter1.docx" \
  -F "file=@chapter2.docx" \
  -F "target_format=pdf" \
  -o docforge_batch_pdf.zip
```

#### PPTX → PDF

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@slides.pptx" \
  -F "target_format=pdf" \
  -o slides.pdf
```

#### Merge multiple documents into one PDF

```bash
curl -X POST http://127.0.0.1:5002/merge \
  -F "file=@intro.docx" \
  -F "file=@appendix.pdf" \
  -F "file=@notes.md" \
  -o docforge_merged.pdf
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
│   │   ├── pptx_to_pdf.py   # LibreOffice converter
│   │   └── txt_to_pdf.py    # WeasyPrint converter
│   ├── services/
│   │   ├── registry.py      # Converter registry
│   │   ├── engine.py        # Conversion orchestration
│   │   ├── file_manager.py  # Upload handling
│   │   └── merger.py        # Document merge workflow
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

## Notes on PPTX → PDF

PPTX → PDF uses LibreOffice in headless mode. Complex slide animations,
embedded media behavior, or highly custom fonts may render differently in the
exported PDF depending on the host LibreOffice installation.

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
