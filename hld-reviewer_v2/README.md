# HLD Reviewer

Automated, credit-efficient review of large HLD PDFs, built around:
- **Backend**: FastAPI (Python), PyMuPDF for chunking, GitHub Models for inference
- **Frontend**: React + Vite
- **AI**: [GitHub Models](https://github.com/marketplace/models) — GitHub's OpenAI-compatible
  inference API. (Note: GitHub Copilot itself has no general-purpose API for arbitrary
  document analysis — its review capability is scoped to PR code review inside GitHub.
  GitHub Models is the actual callable equivalent, and what this project uses.)

## How it keeps credit spend low
1. **Stage 1 (free)** — PDF is chunked into sections locally; nothing is sent to a model yet.
2. **Stage 2 (cheap model)** — every section runs once against a structured checklist prompt
   (`gpt-4o-mini` by default), returning JSON findings.
3. **Stage 3 (escalation only)** — only findings flagged `needs_deep_review` get a second,
   reasoning-heavy pass on a stronger model (`gpt-4o`). Most sections never reach this stage.
4. **Stage 4 (diff-only re-review)** — on a revised HLD, only sections whose text hash changed
   are re-sent to the model at all.

## Setup

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: set GITHUB_TOKEN to a fine-grained PAT with "models: read" permission
# (create one at https://github.com/settings/tokens)
uvicorn app.main:app --reload --port 8000
```

**If your PDFs come from "Print → Save as PDF" (Confluence/wiki exports, etc.):**
these often have no usable text layer — either the content was rasterized, or the
embedded fonts lack a proper text-mapping table. The backend detects this per page and
falls back to OCR automatically, but that needs the Tesseract OCR engine installed
separately (pytesseract is just a wrapper around it):
- **Windows**: install from https://github.com/UB-Mannheim/tesseract/wiki, then make sure
  the install folder (e.g. `C:\Program Files\Tesseract-OCR`) is on your PATH — or set
  `pytesseract.pytesseract.tesseract_cmd` to the full `tesseract.exe` path.
- **macOS**: `brew install tesseract`
- **Linux**: `apt install tesseract-ocr`

OCR is slower and less exact than native text extraction, so if you have any control over
the export, prefer "Print → Save as PDF" settings that embed real text, or export directly
from the wiki (e.g. Confluence's own "Export to PDF" rather than a browser print dialog) —
those usually keep a proper text layer and skip OCR entirely.

### Frontend
```bash
cd frontend
npm install
npm run dev
# open http://localhost:5173
```

## Guided review workflow (primary UI tab)
Matches the Requirement-3 flow: upload → pick sections and focus areas per section →
assign a model per focus area → run → severity-graded summary.

1. `POST /api/extract` — chunk the PDF (free, no model call), returns `doc_id` + section list
2. `GET /api/focus-areas` — focus-area catalog + available models, for the UI's checklist/dropdowns
3. `POST /api/review-selected` — body: `{doc_id, selections: [{chunk_id, focus_areas}], model_assignment: {focus_area: model_key}}`.
   Focus areas assigned to the same model for the same section are combined into a single
   call, so picking three checklist-style focus areas on one section costs one call, not three.

## Quick review workflow (secondary UI tab)
For when you just want everything reviewed without picking sections:
- `POST /api/review` — full review of every section, fixed checklist per section type
- `POST /api/review/{doc_id}/diff` — upload a revised PDF, reviews only changed sections

`GET /api/health` — health check

## Extending
- Tune section detection in `backend/app/pdf_extractor.py` (`SECTION_PATTERNS`) for your
  team's HLD template.
- Add/edit selectable focus areas and their default model/escalation behavior in
  `backend/app/focus_config.py` (`FOCUS_AREAS`, `AVAILABLE_MODELS`).
- Edit the fixed-checklist prompts used by the Quick review tab in `backend/app/checklist.py`.
