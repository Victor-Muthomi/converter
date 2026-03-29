# DocForge

A modular document conversion API built with Flask.

## Supported Conversions

| Input  | Output | Engine              |
|--------|--------|---------------------|
| DOCX   | PDF    | LibreOffice headless|
| PDF    | DOCX   | pdf2docx            |
| HTML   | PDF    | WeasyPrint          |

## System Requirements

- **Python** 3.11+
- **LibreOffice** (for DOCX → PDF conversion)

```bash
# Ubuntu / Debian
sudo apt-get install libreoffice

# WeasyPrint system dependencies
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libcairo2
```

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

#### PDF → DOCX

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@document.pdf" \
  -F "target_format=docx" \
  -o converted.docx
```

#### HTML → PDF

```bash
curl -X POST http://127.0.0.1:5002/convert \
  -F "file=@page.html" \
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
│   │   ├── docx_to_pdf.py   # LibreOffice converter
│   │   ├── pdf_to_docx.py   # pdf2docx converter
│   │   └── html_to_pdf.py   # WeasyPrint converter
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

## License

MIT
