# HLD MHTML Section Selector

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
Open http://localhost:5173.

The extractor independently detects TOC entries and body headings, filters tables/diagrams/OCR-like text, merges by section number, preserves TOC page labels, and reports mismatches.
