"""
Stage 1 — Extract & chunk. Pure text-processing, zero AI-credit cost.
Splits an HLD PDF into logical sections so later stages only send
the relevant chunk to a model instead of the whole document.
"""
import hashlib
import re
from dataclasses import dataclass, field

import fitz  # PyMuPDF

# Below this many characters, a page's native text layer is treated as
# missing/unusable and we fall back to OCR. Browser "print/save as PDF"
# exports (Confluence, wiki pages, etc.) frequently rasterize content or
# embed fonts without a proper ToUnicode map, leaving get_text() empty
# even though the page visibly has text.
MIN_CHARS_PER_PAGE = 20
OCR_ZOOM = 2.0  # ~144 DPI; raise to 3.0 for small/dense text if OCR misses words

# Section header patterns tuned for HLD / Amazon Connect IVR design docs.
# Extend this list as your HLD template evolves.
SECTION_PATTERNS = [
    (r"architecture\s+overview", "architecture_overview"),
    (r"contact\s+flow", "contact_flow_design"),
    (r"call\s+flow", "contact_flow_design"),
    (r"integration", "integrations"),
    (r"lambda", "integrations"),
    (r"security", "security"),
    (r"pci[- ]?dss", "security"),
    (r"authentication", "security"),
    (r"non[- ]?functional|nfr", "nfr"),
    (r"disaster\s+recovery|failover|rollback", "resilience"),
    (r"data\s+flow", "data_flow"),
    (r"error\s+handling|exception", "error_handling"),
]

CHECKLIST_TYPES = {
    "architecture_overview": ["completeness", "consistency"],
    "contact_flow_design": ["contact_flow_correctness", "dtmf_auth"],
    "integrations": ["lambda_integration"],
    "security": ["pci_dss", "dtmf_auth"],
    "nfr": ["nfr"],
    "resilience": ["resilience"],
    "data_flow": ["contact_flow_correctness"],
    "error_handling": ["error_handling"],
    "unclassified": ["completeness"],
}


class ExtractionError(RuntimeError):
    pass


@dataclass
class Chunk:
    id: str
    section_type: str
    heading: str
    text: str
    page_start: int
    page_end: int
    text_hash: str = field(init=False)

    def __post_init__(self):
        self.text_hash = hashlib.sha256(self.text.encode("utf-8")).hexdigest()


def _classify_heading(heading: str) -> str:
    lower = heading.lower()
    for pattern, section_type in SECTION_PATTERNS:
        if re.search(pattern, lower):
            return section_type
    return "unclassified"


def _looks_like_heading(line: str) -> bool:
    """Heuristic: short line, title-case or numbered, no trailing period."""
    line = line.strip()
    if not line or len(line) > 90:
        return False
    if line.endswith((".", ",", ";")):
        return False
    numbered = re.match(r"^(\d+(\.\d+)*)[\.\)]?\s+\S", line)
    titleish = sum(1 for w in line.split() if w[:1].isupper()) >= max(1, len(line.split()) // 2)
    return bool(numbered) or (titleish and len(line.split()) <= 10)


def _ocr_page(page: "fitz.Page") -> str:
    """Rasterize a page and OCR it. Only called when the native text layer is empty/unusable."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise ExtractionError(
            "This page has no extractable text layer (common with browser 'Save as PDF' "
            "exports) and needs OCR, but pytesseract/Pillow aren't installed. Run: "
            "pip install pytesseract Pillow --break-system-packages, and install the "
            "Tesseract OCR engine itself (see README)."
        ) from e

    pix = page.get_pixmap(matrix=fitz.Matrix(OCR_ZOOM, OCR_ZOOM))
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    try:
        return pytesseract.image_to_string(img)
    except pytesseract.TesseractNotFoundError as e:
        raise ExtractionError(
            "Tesseract OCR engine is not installed or not on PATH. On Windows, install it "
            "from https://github.com/UB-Mannheim/tesseract/wiki and ensure the install "
            "directory is in PATH (or set pytesseract.pytesseract.tesseract_cmd)."
        ) from e


def _get_page_text(page: "fitz.Page") -> tuple[str, bool]:
    """Returns (text, was_ocr). Falls back to OCR if the native layer is too sparse to use."""
    native = page.get_text("text")
    if len(native.strip()) >= MIN_CHARS_PER_PAGE:
        return native, False
    return _ocr_page(page), True


def extract_chunks(pdf_path: str) -> list[Chunk]:
    doc = fitz.open(pdf_path)

    # Pull (page_number, line_text) pairs across the whole doc.
    lines: list[tuple[int, str]] = []
    any_ocr = False
    for page_index in range(len(doc)):
        page_text, used_ocr = _get_page_text(doc[page_index])
        any_ocr = any_ocr or used_ocr
        for raw_line in page_text.split("\n"):
            lines.append((page_index + 1, raw_line))
    doc.close()

    if not any(line.strip() for _, line in lines):
        raise ExtractionError(
            "No text could be extracted or OCR'd from this PDF — it may be a blank or "
            "corrupted export. Try re-exporting the source page to PDF."
        )

    chunks: list[Chunk] = []
    current_heading = "Preamble"
    current_lines: list[str] = []
    current_page_start = 1
    chunk_index = 0

    def flush(end_page: int):
        nonlocal chunk_index
        body = "\n".join(current_lines).strip()
        if not body:
            return
        chunk_index += 1
        section_type = _classify_heading(current_heading)
        chunks.append(
            Chunk(
                id=f"chunk_{chunk_index:03d}",
                section_type=section_type,
                heading=current_heading,
                text=body,
                page_start=current_page_start,
                page_end=end_page,
            )
        )

    for page_num, line in lines:
        if _looks_like_heading(line):
            flush(end_page=page_num)
            current_heading = line.strip()
            current_lines = []
            current_page_start = page_num
        else:
            current_lines.append(line)

    flush(end_page=lines[-1][0] if lines else current_page_start)
    return chunks


def diff_changed_chunks(old_chunks: list[Chunk], new_chunks: list[Chunk]) -> list[Chunk]:
    """Stage 4 — only return chunks whose content hash changed or is new."""
    old_hashes = {c.id: c.text_hash for c in old_chunks}
    changed = [c for c in new_chunks if old_hashes.get(c.id) != c.text_hash]
    return changed
