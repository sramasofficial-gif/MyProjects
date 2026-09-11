import os
import shutil
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import storage
from .focus_config import AVAILABLE_MODELS, FOCUS_AREAS
from .pdf_extractor import ExtractionError, diff_changed_chunks, extract_chunks
from .review_engine import review_chunks, review_selected_chunks

app = FastAPI(title="HLD Reviewer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/api/review")
async def review_document(file: UploadFile = File(...)):
    """Full review of a new HLD PDF (or a document you want fully re-reviewed)."""
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}.pdf")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        chunks = extract_chunks(file_path)
    except ExtractionError as e:
        raise HTTPException(422, str(e)) from e

    results = await review_chunks(chunks)
    storage.save_chunks(doc_id, chunks)

    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "sections_reviewed": len(chunks),
        "results": results,
    }


@app.post("/api/review/{doc_id}/diff")
async def review_document_diff(doc_id: str, file: UploadFile = File(...)):
    """Stage 4 — re-review only sections that changed since the last reviewed version."""
    old_chunks = storage.load_chunks(doc_id)
    if old_chunks is None:
        raise HTTPException(404, "No prior version found for this doc_id. Use /api/review first.")

    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}.pdf")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        new_chunks = extract_chunks(file_path)
    except ExtractionError as e:
        raise HTTPException(422, str(e)) from e
    changed_chunks = diff_changed_chunks(old_chunks, new_chunks)

    if not changed_chunks:
        storage.save_chunks(doc_id, new_chunks)
        return {"doc_id": doc_id, "sections_changed": 0, "results": []}

    results = await review_chunks(changed_chunks)
    storage.save_chunks(doc_id, new_chunks)

    return {
        "doc_id": doc_id,
        "sections_reviewed_total": len(new_chunks),
        "sections_changed": len(changed_chunks),
        "results": results,
    }


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Requirement-3 guided workflow: extract -> user selects sections + focus
# areas + models -> review only what was selected -> severity-graded summary.
# ---------------------------------------------------------------------------


@app.get("/api/focus-areas")
async def get_focus_areas():
    """Front-end uses this to render the focus-area checklist and model dropdowns."""
    return {
        "focus_areas": [{"key": k, **v} for k, v in FOCUS_AREAS.items()],
        "available_models": AVAILABLE_MODELS,
    }


@app.post("/api/extract")
async def extract_document(file: UploadFile = File(...)):
    """Stage 1 only — chunk the PDF and return sections for the user to pick from. Zero AI cost."""
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}.pdf")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        chunks = extract_chunks(file_path)
    except ExtractionError as e:
        raise HTTPException(422, str(e)) from e

    storage.save_chunks(doc_id, chunks)

    return {
        "doc_id": doc_id,
        "filename": file.filename,
        "sections": [
            {
                "chunk_id": c.id,
                "heading": c.heading,
                "section_type": c.section_type,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "char_count": len(c.text),
            }
            for c in chunks
        ],
    }


class SectionSelection(BaseModel):
    chunk_id: str
    focus_areas: list[str]


class ReviewSelectedRequest(BaseModel):
    doc_id: str
    selections: list[SectionSelection]
    model_assignment: dict[str, str] = {}


@app.post("/api/review-selected")
async def review_selected(request: ReviewSelectedRequest):
    """Reviews only the sections and focus areas the user checked, using the model
    they assigned per focus area — the economical, user-directed review path."""
    chunks = storage.load_chunks(request.doc_id)
    if chunks is None:
        raise HTTPException(404, "Unknown doc_id. Call /api/extract first.")

    chunks_by_id = {c.id: c for c in chunks}
    selections = [s.model_dump() for s in request.selections]

    if not selections:
        raise HTTPException(400, "No sections selected for review.")

    results = await review_selected_chunks(chunks_by_id, selections, request.model_assignment)

    all_findings = [f for r in results for f in r.get("findings", [])]
    severity_summary = {"high": 0, "medium": 0, "low": 0}
    for f in all_findings:
        sev = f.get("severity", "low")
        if sev in severity_summary:
            severity_summary[sev] += 1

    return {
        "doc_id": request.doc_id,
        "sections_reviewed": len(results),
        "severity_summary": severity_summary,
        "results": results,
    }
