# HLD MHTML Section Selector

Uploads `.mhtml`/`.mht`, extracts the primary HTML part, filters false headings from tables and diagrams, builds a section tree, and displays selectable React checkboxes.

## Backend
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

## Frontend
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`.

## Tests
```powershell
cd backend
python -m pytest -q
```

## Filtering behavior
- A usable Word TOC is authoritative.
- Elements inside table-related tags are rejected.
- Word/HTML drawing, SmartArt, VML, SVG, textbox, canvas, map and object containers are rejected.
- Long, corrupted, punctuation-heavy and OCR/diagram-like blocks are rejected.
- Common column labels are rejected.
- In numbered HLDs, suspicious unnumbered low-level headings are rejected.
