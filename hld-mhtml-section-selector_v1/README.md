# HLD MHTML Section Selector

Full-stack sample that uploads a Word/browser-generated `.mhtml` or `.mht` HLD, extracts its HTML part, detects document sections, and renders selectable checkboxes in a React UI.

## Features

- Drag-and-drop or browse for `.mhtml` and `.mht` files
- Safe in-memory parsing with file-size limits
- Section detection using, in order:
  - Word Table of Contents anchors and TOC-styled paragraphs
  - HTML heading elements (`h1` through `h6`)
  - Word heading styles such as `MsoHeading1` and `Heading 2`
  - Numbered section patterns such as `2`, `2.1`, and `2.1.3`
- Deduplication and hierarchy reconstruction
- Select all, clear all, expand/collapse, and nested selection
- Selected section payload preview ready for a later review endpoint
- Backend unit tests

## Project layout

```text
backend/
  app/main.py
  app/api/routes.py
  app/models/section.py
  app/parsers/mhtml_parser.py
  app/parsers/section_extractor.py
  tests/
frontend/
  src/components/
  src/services/api.js
```

## Run the backend

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

If `py` is unavailable, use the installed Python executable directly.

Backend API documentation: `http://localhost:8000/docs`

## Run the frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The Vite development server proxies `/api` calls to `http://localhost:8000`.

## Run tests

```powershell
cd backend
python -m pytest
```

## API

### `POST /api/v1/documents/extract-sections`

Multipart field name: `file`

Response shape:

```json
{
  "document_name": "sample.mhtml",
  "detection_strategy": "html-headings",
  "section_count": 3,
  "sections": [
    {
      "id": "sec-1",
      "title": "Architecture Overview",
      "level": 1,
      "number": null,
      "page_label": null,
      "source": "h1",
      "children": []
    }
  ],
  "warnings": []
}
```

## Notes

Page numbers are shown only when the MHTML contains a usable TOC page label. MHTML does not inherently preserve reliable PDF-style page boundaries.
