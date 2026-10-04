# MyProjects/IVR_SDLC_Analyst_UI/src/backend/server.py
import shutil
import sys
import json
import os
import re
import subprocess
import pdfplumber
import easyocr
import numpy as np

import traceback
import asyncio # 🟢 Ensure this is imported at the top of server.py
import threading  # 🟢 NEW: Import native thread locking module
import time
import hmac
import hashlib
from pathlib import Path
from datetime import datetime

from pydantic import BaseModel
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Header, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi import Query

from services.repo_tools import read_file  # Import your existing file reader

from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from contextlib import asynccontextmanager

import concurrent.futures
from functools import partial
from review_job_store import ReviewJobStore
import requests

from services.repo_tools import (
    find_files,
    read_file,
    resolve_repository_file
)

from services.flow_audit import (
    audit_contact_flow_file
)

from services.lambda_analysis import (
    analyze_lambda
)

from services.repo_tools import (
    get_repo_tree
)

from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    if sys.platform == "win32":
        try:
            loop = asyncio.get_running_loop()
            print(
                f"[SYSTEM] Active operational loop: {type(loop).__name__}"
            )
        except RuntimeError:
            pass

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

ACTIVE_REVIEW_STATUSES = {
    "QUEUED",
    "RUNNING",
    "CANCEL_REQUESTED",
    "RECOVERY_REQUIRED",
}

DISCOVERABLE_REVIEW_STATUSES = ACTIVE_REVIEW_STATUSES | {"COMPLETED"}

# Cache storage tracking memory arrays
BACKEND_DIAGRAM_CACHE = {}

# Global pointer for temporary state storage between Phase-1 and Phase-2
LATEST_MATRIX_CACHE_PATH = "prioritized_audit_chunks.json"

# 🟢 Global execution pointer referencing our live background Node service thread daemon
LIVE_CO_PROCESS = None

# Persistent long-running HLD review job manager. Browser refreshes do not affect jobs.
# Review job state is intentionally stored outside the source tree.
# The application is developed under OneDrive, and frequently replacing a
# JSON file inside a synced directory can produce WinError 5 when OneDrive
# briefly holds the target file open. Keep this high-frequency state in the
# local AppData area on Windows (or ~/.local/share on non-Windows platforms).
if os.name == "nt":
    _review_state_root = Path(os.environ.get("LOCALAPPDATA", Path.home()))
else:
    _review_state_root = Path.home() / ".local" / "share"

REVIEW_DATA_DIR = _review_state_root / "IVR_SDLC_Analyst_UI"
REVIEW_DATA_DIR.mkdir(parents=True, exist_ok=True)
# Legacy JSON directory is retained only for one-time migration.
REVIEW_JOB_DIR = REVIEW_DATA_DIR / "review_jobs"
REVIEW_JOB_DIR.mkdir(parents=True, exist_ok=True)
REVIEW_DB_PATH = REVIEW_DATA_DIR / "review_jobs.sqlite3"
REVIEW_JOB_STORE = ReviewJobStore(REVIEW_DB_PATH)
REVIEW_JOB_STORE.migrate_json_directory(REVIEW_JOB_DIR)
REVIEW_JOB_LOCK = threading.RLock()
REVIEW_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="hld-review")
REVIEW_CANCEL_EVENTS: dict[str, threading.Event] = {}

# 🟢 CRITICAL DUAL-CALL LOCK PROTECTION: Global re-entrant lock structure
GLOBAL_THREAD_LOCK = threading.RLock()

# Binds paths to local config sheets safely
CONFIG_DIR = Path(__file__).resolve().parent / "conf"
TOOLS_DIR = Path(__file__).resolve().parent / "tools"
SETTINGS_FILE_PATH = os.path.join(CONFIG_DIR, "server_settings.json")
SIMULATION_FILE_PATH = os.path.join(CONFIG_DIR, "simulation_graphs.json")

# --- Confluence Integration Configuration ---
CONFLUENCE_BASE_URL = "https://reqcentral.com" # no trailing slash
AUTH_STATE_FILE = os.path.join(TOOLS_DIR, "entra_auth_state.json")

CONTENT_SELECTORS = [
    "[data-testid='content-body']",  # Confluence Cloud (newer UI)
    "#main-content",                  # Confluence Server/Data Center
    ".ak-renderer-document",          # Confluence Cloud editor renderer
]

class ConfluenceURLRequest(BaseModel):
    page_url: str
    # Phase-1 revision gate controls. The default path always checks the
    # current Confluence document metadata before returning/creating the
    # section matrix. force_refresh is set only after the user explicitly
    # chooses to review an unchanged document version again.
    force_refresh: bool = False

# 1. Map Schema models for the Wiki extraction payload boundaries
class HLDIngestionRequest(BaseModel):
    document_title: str
    raw_content: str = ""
    project_scope: Optional[str] = "IVR Context Validation"
    review_scopes: list[str] = []
    selected_section_ids: list[int] = []


class HLDReviewStartRequest(BaseModel):
    document_title: str
    review_scopes: list[str] = []
    force_new_review: bool = False
    selected_section_ids: list[int] = []
    project_scope: Optional[str] = "IVR Context Validation"
    source_version: Optional[str] = None
    source_version_timestamp: Optional[str] = None
    source_version_source: Optional[str] = None
    document_last_updated: Optional[str] = None
    document_last_updated_by: Optional[str] = None
    document_created_by: Optional[str] = None
    source_content_hash: Optional[str] = None
    review_type: Optional[str] = "Technical Document Review"
    review_plan: dict = {}


class DiagramGenerationRequest(BaseModel):
    file_path: str
    file_content: str
    diagram_type: str

# 1. Define Server Controls Configuration Model State Schema
class SystemSettingsProfile(BaseModel):
    enable_diagram_caching: bool = True
    enable_simulation_mode: bool = True
    enable_persistence: bool = True

async def _find_content_selector_async(page):
    for selector in CONTENT_SELECTORS:
        # 🟢 FIX: Await locator count verification steps
        if await page.locator(selector).count() > 0:
            return selector
    return "body"

async def ensure_full_content_loaded_async(page, max_scroll_passes=40, settle_ms=600):
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
        
    prev_height = -1
    for _ in range(max_scroll_passes):
        curr_height = await page.evaluate("document.body.scrollHeight")
        if curr_height == prev_height:
            break
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(settle_ms)
        prev_height = curr_height
        
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(settle_ms)
    
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
        
    for frame in page.frames:
        try:
            await frame.wait_for_load_state("load", timeout=5000)
        except Exception:
            pass
            
    await page.wait_for_timeout(500)

# ==============================================================================
# 🟢 ENHANCEMENT: FILE PERSISTENCE LIFECYCLE CONTROLLERS
# ==============================================================================
def load_persisted_settings() -> SystemSettingsProfile:
    """Reads configuration data from a JSON file on initialization."""
    print(f"[INFO] Settings path set to:  {SETTINGS_FILE_PATH}")
    if os.path.exists(SETTINGS_FILE_PATH):
        try:
            with open(SETTINGS_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[⚙️ CONFIG LAUNCH] Successfully loaded settings profile from disk.")
                return SystemSettingsProfile(**data)
        except Exception as e:
            print(f"[⚠️ CONFIG ERROR] Failed to load server_settings.json, falling back to defaults: {e}")
    return SystemSettingsProfile()

def save_settings_to_file(settings: SystemSettingsProfile):
    """Writes active configurations directly out to hard text files."""
    try:
        with open(SETTINGS_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(settings.dict(), f, indent=2)
        print("[⚙️ CONFIG SYNCHRONIZED] settings profile committed safely to server_settings.json")
    except Exception as e:
        print(f"[⚠️ PERSIST FAILURE] Could not write system configurations to disk: {e}")

def get_simulated_graph(file_name: str, graph_type: str) -> str:
    """Scans the simulation matrix for matching file and diagram keys."""
    if not os.path.exists(SIMULATION_FILE_PATH):
        print(f"[⚠️ SIMULATION WARNING] simulation_graphs.json file missing at {SIMULATION_FILE_PATH}")
        return None
        
    try:
        with open(SIMULATION_FILE_PATH, "r", encoding="utf-8") as f:
            mock_records = json.load(f)
            
        # Normalize incoming string values to prevent casing mismatches
        target_file = file_name.strip().lower().replace('\\', '/')
        target_type = graph_type.strip().lower()

        print(f"[SIMULATION CHECK] Finding matching record for file '{file_name}' and graph type '{graph_type}' in {SIMULATION_FILE_PATH}")
        
        for record in mock_records:
            current_file = record.get("file_name", "").strip().lower().replace('\\', '/')
            current_type = record.get("graph_type", "").strip().lower()
            
            if current_file == target_file and current_type == target_type:
                return record.get("mermaid_string", "").strip()
    except Exception as e:
        print(f"[⚠️ OCR/SIMULATION ERROR] Breakdown reading simulation ledger: {e}")
        
    return None

# Global structural memory state tracking initialized straight from local persistent file
SERVER_CONFIG = load_persisted_settings()

# Global structural memory state tracking variable pointer initialization
#SERVER_CONFIG = SystemSettingsProfile()

# Re-use your optimized classes within the server pipeline framework
class DynamicPDFExtractor:
    """Checks for a digital font layer before choosing a parallelized parsing framework."""
    def __init__(self, file_path: str):
        self.file_path = file_path

    def _ocr_single_page(self, page_index: int) -> str:
        """Isolated single-page worker loop designed for explicit parallel thread execution."""
        # Clean local import scope initialized per active core pipeline thread instance
        import pdfplumber
        import easyocr
        import numpy as np

        print(f"    ↳ [⚡ Thread Worker] Starting local OCR scanning for Page {page_index + 1}...")
        
        # Initialize an isolated execution engine inside the worker thread boundaries
        reader = easyocr.Reader(['en'], gpu=False)
        
        with pdfplumber.open(self.file_path) as pdf:
            page = pdf.pages[page_index]
            page_image = page.to_image(resolution=150)
            img_np = np.array(page_image.original)
            strings = reader.readtext(img_np, detail=0)
            
            if strings:
                return "\n".join(strings) + "\n"
        return ""

    def extract_clean_text(self) -> str:
        text_content = []
        
        # 1. Attempt digital text layer parsing first
        print(f"[🔍] Evaluating digital text layer via pdfplumber: {self.file_path}")
        with pdfplumber.open(self.file_path) as pdf:
            total_pages = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text + "\n")
                    
        raw_digital_text = "".join(text_content).strip()
        
        if len(raw_digital_text) > 50:
            print(f"[✔] Native text layer detected ({len(raw_digital_text)} chars). Skipping Parallel OCR.")
            return raw_digital_text

        # 2. Fallback to High-Performance Parallel OCR if native text layer is missing
        print(f"[⚡] Scanned PDF Canvas detected. Initializing Parallel OCR Thread Pool across {total_pages} pages...")
        
        ocr_results = [None] * total_pages
        
        # Maximize context workers using safe computing thresholds (e.g., up to 4 parallel tracks)
        max_workers = min(4, os.cpu_count() or 2)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Bind the processing matrix mapping tracking boundaries
            page_indices = list(range(total_pages))
            results = executor.map(self._ocr_single_page, page_indices)
            
            for idx, text_result in enumerate(results):
                ocr_results[idx] = text_result

        # Final assembly combining chronological fragments into full document
        print("[✔] Concurrent page execution segments complete. Compiling final core layout document...")
        return "\n\n".join(filter(None, ocr_results))
    
class HLDAuditChunker:
    """Splits structural components into context-aware chunks for LLM security analysis."""
    def __init__(self, target_chunk_size=1200, overlap=200):
        self.chunk_size = target_chunk_size
        self.overlap = overlap
        
        # Flexed header pattern for varying OCR layouts
        self.header_pattern = re.compile(
            r'(?m)^(?:\d+(?:\.\d+)*\s+[A-Z\s]{4,}|SECTION\s+[A-Z\d]+:?.*)$', 
            re.IGNORECASE
        )
        
        self.audit_keywords = {
            "security": ["iam", "auth", "encryption", "tls", "rbac", "token", "secrets", "kms", "firewall", "vpc", "dmz"],
            "integration": ["api", "webhook", "grpc", "kafka", "mq", "payload", "schema", "rest", "endpoint", "middleware"]
        }

    def _extract_sections(self, text: str) -> list:
        matches = list(self.header_pattern.finditer(text))
        
        # FIX 1: Safe exit loop if no structural header match targets exist
        if not matches:
            return [["Scanned Layout / Complete HLD Stream", text]]
        
        sections = []
        # FIX 2: Protected index check initialization
        if matches[0].start() > 0:
            sections.append(["Preamble / Introduction", text[:matches[0].start()]])
            
        for i in range(len(matches)):
            start = matches[i].start()
            end = matches[i+1].start() if i + 1 < len(matches) else len(text)
            header_title = matches[i].group(0).strip()
            sections.append([header_title, text[start:end]])
        return sections

    def _tag_chunk_focus(self, chunk_text: str) -> list:
        lower_text = chunk_text.lower()
        tags = []
        for domain, keywords in self.audit_keywords.items():
            if any(kw in lower_text for kw in keywords):
                tags.append(domain.upper())
        return tags

    def create_audit_chunks(self, raw_text: str) -> list:
        structured_sections = self._extract_sections(raw_text)
        final_chunks = []
        
        for header, section_content in structured_sections:
            words = section_content.split()
            
            if len(words) <= self.chunk_size:
                tags = self._tag_chunk_focus(section_content)
                final_chunks.append({
                    "metadata": {"parent_section": header, "audit_tags": tags},
                    "content": f"[Context: {header}] [Focus: {', '.join(tags)}]\n{section_content}"
                })
                continue
                
            start_idx = 0
            while start_idx < len(words):
                end_idx = start_idx + self.chunk_size
                chunk_words = words[start_idx:end_idx]
                chunk_text = " ".join(chunk_words)
                
                tags = self._tag_chunk_focus(chunk_text)
                final_chunks.append({
                    "metadata": {"parent_section": header, "audit_tags": tags, "split_block": True},
                    "content": f"[Context: {header} (Cont.)] [Focus: {', '.join(tags)}]\n{chunk_text}"
                })
                start_idx += (self.chunk_size - self.overlap)
                
        return final_chunks


def minimize_source_code(source_code: str) -> str:
    """
    Strips single-line and multi-line comments, compresses vertical whitespaces,
    and clears out empty trailing line padding to minimize token footprint consumption.
    """
    if not source_code:
        return ""
        
    # 1. Strip multi-line block comments: /* ... */
    code = re.sub(r'/\*[\s\S]*?\*/', '', source_code)
    
    # 2. Strip single-line comments: // ..., ignoring protocols like http:// or https://
    lines = []
    for line in code.splitlines():
        cleaned_line = re.sub(r'(?<!:)\/\/.*$', '', line)
        lines.append(cleaned_line)
    code = "\n".join(lines)
    
    # 3. Collapse multiple sequential blank lines down to a clean singular newline split
    code = re.sub(r'\n\s*\n', '\n', code)
    
    # 4. Remove leading/trailing indentation blocks per active functional string row
    compact_lines = [line.strip() for line in code.splitlines() if line.strip()]
    
    return "\n".join(compact_lines)

# ---------------------------------------------------------------------------
# Confluence section inventory extraction (ported from confluence_wiki_reader.py)
# ---------------------------------------------------------------------------
# This intentionally mirrors the original rendered-DOM identification logic:
# headings are walked in DOM order and each section is classified by the
# rendered elements found until the next heading.
SECTION_EXTRACT_JS = r"""
(containerSelector) => {
    const container = document.querySelector(containerSelector) || document.body;

    const relevant = container.querySelectorAll(
        'h1,h2,h3,h4,h5,h6,table,.table-wrap,img,svg,canvas,iframe,' +
        '.confluence-embedded-image,.image-wrap,.confluence-embedded-file-wrapper,' +
        '[class*="drawio" i],[class*="gliffy" i],[class*="diagram" i],' +
        '[data-macro-name],.macro-placeholder,p,ul,ol'
    );

    const headings = Array.from(container.querySelectorAll('h1,h2,h3,h4,h5,h6'));
    const sections = [];
    let current = null;
    const preHeadingContent = { types: new Set(), placeholders: 0 };

    const isEmptyShell = (el) => {
        const txt = (el.innerText || '').trim();
        const hasMedia = el.querySelector('img,svg,canvas,iframe');
        return txt.length === 0 && !hasMedia;
    };

    const isVisualElement = (el) => {
        const tag = el.tagName.toLowerCase();
        const directMedia = tag === 'img' || tag === 'svg' || tag === 'canvas' || tag === 'iframe';
        const embeddedImage = el.classList.contains('confluence-embedded-image') || el.classList.contains('image-wrap');
        const diagramContainer = [...el.classList].some(c => /drawio|gliffy|visio|diagram/i.test(c));

        // Capture the actual rendered media element when possible. If a diagram is
        // represented only by a wrapper/container, capture that wrapper instead.
        if (directMedia || embeddedImage) return true;
        if (diagramContainer) {
            return !el.querySelector('img,svg,canvas,iframe');
        }
        return false;
    };

    const extractAssetCandidates = (el) => {
        const candidates = [];
        const add = (value, kind) => {
            if (!value) return;
            const raw = String(value).trim();
            if (!raw || raw.startsWith('data:') || raw.startsWith('blob:')) return;
            try {
                const absolute = new URL(raw, window.location.href).href;
                if (!candidates.some(c => c.url === absolute)) {
                    candidates.push({ url: absolute, kind });
                }
            } catch (_) {}
        };

        ['src', 'data-src', 'data-image-src', 'data-full-src', 'data-original', 'data-original-src'].forEach(attr => {
            add(el.getAttribute(attr), attr);
        });

        const srcset = el.getAttribute('srcset');
        if (srcset) {
            srcset.split(',').forEach(part => {
                const url = part.trim().split(/\s+/)[0];
                add(url, 'srcset');
            });
        }

        const parentLink = el.closest('a[href]');
        if (parentLink) {
            add(parentLink.getAttribute('href'), 'parent-link');
        }

        return candidates;
    };

    let sectionIndex = 0;

    for (const el of relevant) {
        const tag = el.tagName.toLowerCase();

        if (/^h[1-6]$/.test(tag)) {
            if (current) sections.push(current);
            sectionIndex += 1;
            const raw = (el.innerText || '').trim();
            const numMatch = raw.match(/^([0-9]+(\.[0-9]+)*)/);
            current = {
                index: sectionIndex,
                level: parseInt(tag.slice(1), 10),
                heading: raw,
                numbering: numMatch ? numMatch[1] : null,
                types: new Set(),
                placeholderCount: 0,
                domId: el.id || null,
                visualElements: []
            };
            el.setAttribute('data-hld-section-heading-index', String(sectionIndex));
            continue;
        }

        const bucket = current || preHeadingContent;

        if (tag === 'table' || el.classList.contains('table-wrap')) {
            bucket.types.add('table');
        } else if (tag === 'iframe') {
            bucket.types.add('diagram-iframe');
            if (isEmptyShell(el)) bucket.placeholderCount = (bucket.placeholderCount || 0) + 1;
        } else if (
            tag === 'img' || tag === 'svg' || tag === 'canvas' ||
            el.classList.contains('confluence-embedded-image') ||
            el.classList.contains('image-wrap')
        ) {
            bucket.types.add('image');
        } else if ([...el.classList].some(c => /drawio|gliffy|visio|diagram/i.test(c))) {
            bucket.types.add('diagram');
            if (isEmptyShell(el)) bucket.placeholderCount = (bucket.placeholderCount || 0) + 1;
        } else if (el.classList.contains('macro-placeholder')) {
            bucket.types.add('unresolved-macro');
            bucket.placeholderCount = (bucket.placeholderCount || 0) + 1;
        } else if (el.hasAttribute('data-macro-name')) {
            const macroName = el.getAttribute('data-macro-name') || '';
            if (/gliffy|drawio|visio|diagram/i.test(macroName)) {
                bucket.types.add('diagram');
            } else {
                bucket.types.add('macro:' + macroName);
            }
        } else if (tag === 'p' || tag === 'ul' || tag === 'ol') {
            if ((el.innerText || '').trim().length > 0) bucket.types.add('text');
        }

        if (current && isVisualElement(el)) {
            el.setAttribute('data-hld-section-visual', String(current.index));
            current.visualElements.push({
                tag,
                domId: el.id || null,
                className: typeof el.className === 'string' ? el.className : '',
                alt: el.getAttribute('alt') || null,
                title: el.getAttribute('title') || null,
                assetCandidates: extractAssetCandidates(el),
                iframeSrc: tag === 'iframe' ? (el.getAttribute('src') || null) : null
            });
        }
    }
    if (current) sections.push(current);

    sections.forEach((section, index) => {
        const headingEl = headings[index];
        const nextHeadingEl = headings[index + 1] || null;
        if (!headingEl) {
            section.content = '';
            return;
        }

        const range = document.createRange();
        range.setStartBefore(headingEl);
        if (nextHeadingEl) range.setEndBefore(nextHeadingEl);
        else range.setEndAfter(container.lastChild || headingEl);

        const wrapper = document.createElement('div');
        wrapper.appendChild(range.cloneContents());
        section.content = (wrapper.innerText || '').trim();
    });

    return {
        preHeadingTypes: Array.from(preHeadingContent.types),
        sections: sections.map(s => ({
            level: s.level,
            heading: s.heading,
            numbering: s.numbering,
            types: Array.from(s.types),
            placeholderCount: s.placeholderCount,
            domId: s.domId,
            content: s.content || '',
            visualElements: s.visualElements || []
        }))
    };
}
"""

TYPE_LABELS = {
    "table": "Table",
    "image": "Image",
    "diagram": "Diagram",
    "diagram-iframe": "Diagram (iframe)",
    "text": "Text",
    "unresolved-macro": "Unresolved macro",
}

MATRIX_SCHEMA_VERSION = 5
HLD_VISUAL_CACHE_DIR = Path(__file__).resolve().parent / "hld_visual_cache"
HLD_REPORTS_DIR = Path(__file__).resolve().parent / "hld_reports"
HLD_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Lazy OCR reader used only on the small top strip of exported interactive diagrams.
# It is intentionally initialized on first use so normal HLD scraping does not pay
# the OCR startup cost.
_HEADING_OCR_READER = None

# Review scopes used to route HLD sections to an appropriate AI review strategy.
REVIEW_SCOPE_DEFINITIONS = {
    "functional": {
        "label": "Functional Completeness",
        "types": {"text", "table"},
        "keywords": ["requirement", "business", "objective", "scope", "use case", "functional", "workflow", "acceptance"],
    },
    "architecture": {
        "label": "Architecture",
        "types": {"text", "table", "diagram", "diagram-iframe", "image"},
        "keywords": ["architecture", "solution", "component", "logical", "physical", "deployment", "data flow", "information model", "topology", "design"],
        "diagram_always": True,
    },
    "security": {
        "label": "Security",
        "types": {"text", "table", "diagram", "diagram-iframe"},
        "keywords": ["security", "authentication", "authorization", "iam", "permission", "encryption", "secret", "tls", "rbac", "credential", "pci", "pii", "access control"],
    },
    "vulnerability": {
        "label": "Vulnerability",
        "types": {"text", "table", "diagram", "diagram-iframe"},
        "keywords": ["vulnerability", "threat", "attack", "injection", "cve", "penetration", "exploit", "risk"],
    },
    "performance": {
        "label": "Performance",
        "types": {"text", "table", "diagram", "diagram-iframe"},
        "keywords": ["performance", "latency", "throughput", "capacity", "load", "concurrency", "response time", "sla", "scalability"],
    },
    "reliability": {
        "label": "Reliability & Availability",
        "types": {"text", "table", "diagram", "diagram-iframe"},
        "keywords": ["availability", "resilience", "failover", "retry", "timeout", "disaster recovery", "backup", "recovery", "fault", "redundancy", "high availability"],
    },
    "integration": {
        "label": "Integration",
        "types": {"text", "table", "diagram", "diagram-iframe"},
        "keywords": ["integration", "api", "webhook", "lambda", "kinesis", "s3", "dynamodb", "lex", "amazon connect", "endpoint", "interface", "payload", "queue", "event", "middleware"],
    },
    "compliance": {
        "label": "Compliance",
        "types": {"text", "table"},
        "keywords": ["compliance", "pci", "gdpr", "hipaa", "retention", "audit", "regulatory", "standard", "policy", "record keeping"],
    },
    "documentation": {
        "label": "Documentation Quality",
        "types": {"text", "table", "diagram", "diagram-iframe", "image"},
        "keywords": ["overview", "purpose", "scope", "definition", "glossary", "reference", "document", "appendix", "assumption", "terminology"],
    },
    "testability": {
        "label": "Testability",
        "types": {"text", "table", "diagram", "diagram-iframe"},
        "keywords": ["test", "testing", "validation", "qa", "acceptance", "mock", "automation", "test case", "quality"],
    },
    "cost": {
        "label": "Cost Optimization",
        "types": {"text", "table"},
        "keywords": ["cost", "pricing", "budget", "finops", "sizing", "resource", "consumption", "license"],
    },
    "ivr": {
        "label": "IVR / Contact Center",
        "types": {"text", "table", "diagram", "diagram-iframe"},
        "keywords": ["ivr", "contact flow", "amazon connect", "lambda", "lex", "queue", "caller", "prompt", "dtmf", "transfer", "disconnect", "contact center", "agent"],
    },
}

class HLDExcelExportRequest(BaseModel):
    document_title: str
    review_result: dict
    selected_section_ids: list[int] = []


class HLDReviewPlanRequest(BaseModel):
    document_title: str
    review_scopes: list[str] = []
    selected_section_ids: list[int] = []


async def extract_confluence_source_metadata_async(page, page_url: str) -> dict:
    """Extract the source timestamp shown in the visible Confluence page header.

    Preference order:
      1. Visible page-header text: "Created by ..., last updated by ... on ..."
      2. Confluence meta/time elements for the modified timestamp
      3. Scrape timestamp as an observation fallback (never presented as document last-updated)
    """
    observed_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    try:
        data = await page.evaluate("""() => {
            const text = document.body?.innerText || '';
            const clean = value => (value || '').replace(/\s+/g, ' ').trim();

            let createdBy = null;
            let lastUpdatedBy = null;
            let lastUpdated = null;

            const headerMatch = text.match(
                /Created\s+by\s+(.+?),\s*last\s+updated\s+by\s+(.+?)\s+on\s+([^\n•|]+?)(?:\s+•|\n|$)/i
            );
            if (headerMatch) {
                createdBy = clean(headerMatch[1]);
                lastUpdatedBy = clean(headerMatch[2]);
                lastUpdated = clean(headerMatch[3]);
            }

            const pick = selectors => {
                for (const selector of selectors) {
                    const el = document.querySelector(selector);
                    if (!el) continue;
                    const value = el.getAttribute('content') ||
                        el.getAttribute('datetime') ||
                        el.textContent;
                    if (value && clean(value)) return clean(value);
                }
                return null;
            };

            const metaModified = pick([
                'meta[property="article:modified_time"]',
                'meta[name="last-modified"]',
                'meta[name="ajs-content-last-updated"]',
                'time[datetime]'
            ]);

            const title = pick([
                'meta[property="og:title"]',
                'meta[name="ajs-content-title"]',
                'title'
            ]);

            const version = pick([
                '[data-version-number]',
                '[data-page-version]',
                '[data-version]',
                'meta[name="ajs-page-version"]',
                'meta[name="page-version"]',
                'meta[property="page:version"]'
            ]);

            return {
                title,
                version,
                createdBy,
                lastUpdatedBy,
                lastUpdated,
                metaModified
            };
        }""")
    except Exception as exc:
        print(f"[SOURCE METADATA] Extraction failed: {exc}")
        data = {}

    title = str(data.get("title") or "").strip() or None
    version = str(data.get("version") or "").strip() or None
    created_by = str(data.get("createdBy") or "").strip() or None
    last_updated_by = str(data.get("lastUpdatedBy") or "").strip() or None
    last_updated = str(data.get("lastUpdated") or "").strip() or None
    meta_modified = str(data.get("metaModified") or "").strip() or None

    if last_updated:
        timestamp_source = "confluence_page_header"
    elif meta_modified:
        # This is a Confluence modified timestamp, but not necessarily the human-visible header value.
        last_updated = meta_modified
        timestamp_source = "confluence_modified_metadata"
    else:
        timestamp_source = "scrape_timestamp"

    return {
        "document_url": page_url,
        "document_title": title or page_url,
        "document_version": version,
        "document_version_timestamp": meta_modified,
        "document_version_source": "confluence_page_version" if version else None,
        "document_last_updated": last_updated,
        "document_last_updated_by": last_updated_by,
        "document_created_by": created_by,
        "document_last_updated_source": timestamp_source,
        "observed_at": observed_at,
    }


# --- Phase 1: Ingestion & Matrix Compiling Endpoint ---
def get_file_cache_path(filename: str) -> str:
    """Generates an isolated storage filename based on the document name."""
    # Sanitize filename to prevent directory traversal issues
    safe_name = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in ['.', '_', '-']]).strip()
    return f"matrix_cache_{safe_name}.json"


def get_wiki_cache_path(page_url: str) -> str:
    """Returns the Phase-1 cache path used by the Confluence URL workflow."""
    url_hash = hashlib.sha256(page_url.encode("utf-8")).hexdigest()
    return f"matrix_cache_wiki_v{MATRIX_SCHEMA_VERSION}_{url_hash[:16]}.json"

def _normalise_review_scopes(review_scopes: list[str] | None) -> list[str]:
    return sorted({
        str(scope).strip().lower()
        for scope in (review_scopes or [])
        if str(scope).strip() in REVIEW_SCOPE_DEFINITIONS
    })


def _normalise_section_ids(section_ids: list[int] | None) -> list[int]:
    values = []
    for value in section_ids or []:
        try:
            values.append(int(value))
        except (TypeError, ValueError):
            continue
    return sorted(set(values))


def _get_eligible_section_ids(
    document_title: str,
    review_scopes: list[str] | None,
    selected_section_ids: list[int] | None,
) -> list[int]:
    """Resolve the exact section set used by Review Plan and Review Start.

    This must be the single source of truth for review signatures and active-job
    discovery so browser recovery cannot accidentally attach to a different
    section/scope combination.
    """
    scopes = _normalise_review_scopes(review_scopes)
    selected_ids = set(_normalise_section_ids(selected_section_ids))
    matrix_chunks = _load_cached_hld_matrix(document_title)

    eligible_ids = []
    for chunk in matrix_chunks:
        section_id = int(chunk.get("id", 0))
        status = (chunk.get("metadata") or {}).get("status") or chunk.get("status") or "ok"

        if selected_ids and section_id not in selected_ids:
            continue
        if status == "empty":
            continue
        if not _section_matches_scopes(chunk, scopes):
            continue

        eligible_ids.append(section_id)

    return sorted(set(eligible_ids))


def _review_signature(
    document_title: str,
    review_scopes: list[str] | None,
    eligible_section_ids: list[int] | None,
) -> str:
    """Canonical v2 signature shared by plan, start, resume and discovery."""
    payload = {
        "document_title": str(document_title or "").strip(),
        "matrix_schema_version": MATRIX_SCHEMA_VERSION,
        "review_scopes": _normalise_review_scopes(review_scopes),
        "eligible_section_ids": _normalise_section_ids(eligible_section_ids),
    }

    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _legacy_review_signature(
    document_title: str,
    review_scopes: list[str] | None,
    eligible_section_ids: list[int] | None,
) -> str:
    """Compatibility signature used by jobs created before active-job discovery was added."""
    payload = {
        "document_title": str(document_title or "").strip(),
        "matrix_schema_version": MATRIX_SCHEMA_VERSION,
        "review_scopes": sorted(set(review_scopes or [])),
        "eligible_section_ids": sorted({int(x) for x in (eligible_section_ids or [])}),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _job_matches_review_request(
    job: dict,
    document_title: str,
    review_scopes: list[str] | None,
    eligible_section_ids: list[int] | None,
) -> bool:
    """Match a persisted job against the same canonical review request."""
    target_signature = _review_signature(
        document_title,
        review_scopes,
        eligible_section_ids,
    )
    legacy_signature = _legacy_review_signature(
        document_title,
        review_scopes,
        eligible_section_ids,
    )

    stored_signature = str(job.get("review_signature") or "")
    if stored_signature in {target_signature, legacy_signature}:
        return True

    # Fallback for very old records that did not persist a signature.
    job_document = str(
        job.get("document_title") or job.get("document_url") or ""
    ).strip()
    job_scopes = _normalise_review_scopes(job.get("review_scopes") or [])
    job_eligible = _normalise_section_ids(
        job.get("eligible_section_ids") or job.get("selected_section_ids") or []
    )
    return (
        job_document == str(document_title or "").strip()
        and job_scopes == _normalise_review_scopes(review_scopes)
        and job_eligible == _normalise_section_ids(eligible_section_ids)
    )


def _discover_active_review_job(
    document_title: str,
    review_scopes: list[str] | None,
    selected_section_ids: list[int] | None,
):
    """Return the newest discoverable review job matching the exact request."""
    eligible_ids = _get_eligible_section_ids(
        document_title,
        review_scopes,
        selected_section_ids,
    )
    signature = _review_signature(
        document_title,
        _normalise_review_scopes(review_scopes),
        _normalise_section_ids(eligible_ids),
    )
    try:
        jobs, _ = REVIEW_JOB_STORE.list_jobs(limit=500, offset=0)
        candidates = [
            job for job in jobs
            if job.get("status") in DISCOVERABLE_REVIEW_STATUSES
            and job.get("review_signature") == signature
            and _job_matches_review_request(
                job, document_title, review_scopes, eligible_ids
            )
        ]
        if not candidates:
            return None
        candidates.sort(
            key=lambda item: str(
                item.get("updated_at") or item.get("created_at") or ""
            ),
            reverse=True,
        )
        return candidates[0]
    except Exception as exc:
        print(f"[REVIEW JOB] Active discovery failed: {exc}")
        return None


@app.get("/api/hld/review/active")
async def discover_active_hld_review(
    document_url: str = Query(..., description="HLD/Confluence document URL"),
    review_scopes: Optional[str] = Query(None),
    selected_section_ids: Optional[str] = Query(None),
):
    """Find an active, recoverable, or completed review for the exact request."""
    scopes = [
        item.strip().lower()
        for item in (review_scopes or "").split(",")
        if item.strip()
    ]

    section_ids = []
    for value in (selected_section_ids or "").split(","):
        value = value.strip()
        if not value:
            continue
        try:
            section_ids.append(int(value))
        except ValueError:
            continue

    job = _discover_active_review_job(
        document_title=document_url,
        review_scopes=scopes,
        selected_section_ids=section_ids,
    )

    return {
        "success": True,
        "found": bool(job),
        "job": _job_public_view(job),
    }

async def extract_confluence_section_inventory_async(page, selector):
    """
    Extract the section inventory from the rendered Confluence DOM.

    SECTION_EXTRACT_JS is expected to return an array containing one record
    per HLD section with fields such as:
      - heading
      - content
      - types
      - status
      - level
      - numbering
      - placeholderCount
      - domId
    """
    if not selector:
        selector = "body"

    result = await page.evaluate(
        SECTION_EXTRACT_JS,
        selector,
    )

    if not isinstance(result, list):
        raise ValueError(
            "SECTION_EXTRACT_JS did not return a list of section records."
        )

    rows = []

    for index, raw_row in enumerate(result, start=1):
        row = dict(raw_row or {})

        row.setdefault(
            "id",
            index,
        )

        row.setdefault(
            "heading",
            "Unclassified section",
        )

        row.setdefault(
            "content",
            "",
        )

        row.setdefault(
            "types",
            [],
        )

        row.setdefault(
            "status",
            "empty" if not row.get("types") else "ok",
        )

        row.setdefault(
            "level",
            0,
        )

        row.setdefault(
            "numbering",
            "",
        )

        row.setdefault(
            "placeholderCount",
            0,
        )

        row.setdefault(
            "domId",
            "",
        )

        # Normalize types.
        types = row.get("types")

        if not isinstance(types, list):
            types = (
                list(types)
                if isinstance(types, (set, tuple))
                else []
            )

        row["types"] = [
            str(value).strip().lower()
            for value in types
            if str(value).strip()
        ]

        # Preserve visual evidence fields expected by the
        # downstream Copilot-review workflow.
        row.setdefault(
            "visual_evidence",
            [],
        )

        row.setdefault(
            "visual_review_available",
            False,
        )

        row.setdefault(
            "visual_review_analyzed",
            False,
        )

        rows.append(row)

    print(
        f"[SECTION EXTRACTION] Extracted "
        f"{len(rows)} section(s) from rendered DOM."
    )

    return rows

@app.post("/api/hld/generate-matrix")
async def generate_verified_matrix(payload: ConfluenceURLRequest):
    """
    Phase 1: metadata-first document ingestion gate followed by section matrix extraction.

    Normal flow:
      1. Open the authenticated Confluence page.
      2. Extract the visible document last-updated metadata only.
      3. Check SQLite for a completed review of the same document revision.
      4. If one exists, return a confirmation gate without extracting sections.
      5. Otherwise, reuse a cache only when its stored document timestamp matches.
      6. If extraction is required, continue with full content + visual capture.

    force_refresh=True is used only after an explicit user decision to review the
    unchanged document version again, or by the explicit Re-Scrape workflow.
    """
    page_url = payload.page_url.strip()
    if not page_url:
        raise HTTPException(status_code=400, detail="Missing Confluence page URL.")

    url_hash = hashlib.sha256(page_url.encode("utf-8")).hexdigest()
    target_cache_path = get_wiki_cache_path(page_url)
    cache_metadata_path = Path(str(target_cache_path) + ".meta.json")

    if not os.path.exists(AUTH_STATE_FILE):
        raise HTTPException(
            status_code=401,
            detail=f"No saved Confluence session found ({AUTH_STATE_FILE}). Run login locally first.",
        )

    browser = None
    try:
        # ------------------------------------------------------------
        # LIGHTWEIGHT REVISION CHECK
        # ------------------------------------------------------------
        # Do not call ensure_full_content_loaded_async() here. We only need
        # enough of the page to read the title / last-updated metadata.
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                storage_state=AUTH_STATE_FILE,
                viewport={"width": 1920, "height": 1200},
                device_scale_factor=1,
            )
            page = await context.new_page()
            await page.goto(page_url, wait_until="domcontentloaded")
            try:
                await page.wait_for_timeout(750)
            except Exception:
                pass

            source_metadata = await extract_confluence_source_metadata_async(page, page_url)

            if not source_metadata.get("document_title"):
                source_metadata["document_title"] = page_url

            current_last_updated = str(
                source_metadata.get("document_last_updated") or ""
            ).strip()

            # --------------------------------------------------------
            # EXISTING COMPLETED REVIEW GATE
            # --------------------------------------------------------
            if current_last_updated:
                existing_completed = REVIEW_JOB_STORE.find_latest_completed_by_document_revision(
                    document_url=page_url,
                    document_last_updated=current_last_updated,
                )
            else:
                existing_completed = None

            if existing_completed and not payload.force_refresh:
                print(
                    "[DOCUMENT REVISION GATE] Completed review already exists: "
                    f"job={existing_completed.get('job_id')} "
                    f"updated={current_last_updated}"
                )
                await browser.close()
                browser = None
                return {
                    "success": True,
                    "requires_confirmation": True,
                    "confirmation_type": "existing_completed_review",
                    "message": (
                        "A completed review already exists for the current Confluence "
                        "document timestamp. No section matrix extraction was performed."
                    ),
                    "filename": page_url,
                    "matrix": [],
                    "loaded_from_cache": False,
                    "source_metadata": source_metadata,
                    "existing_review": _job_public_view(existing_completed),
                    "cache_available": os.path.exists(target_cache_path),
                }

            # --------------------------------------------------------
            # CACHE REUSE CHECK
            # --------------------------------------------------------
            # Only reuse an existing matrix when its source metadata matches
            # the current Confluence last-updated timestamp. This prevents a
            # stale URL-only cache from silently hiding a changed document.
            cache_usable = False
            cached_matrix = None
            cached_metadata = None

            if (
                SERVER_CONFIG.enable_persistence
                and os.path.exists(target_cache_path)
                and cache_metadata_path.exists()
                and not payload.force_refresh
            ):
                try:
                    with cache_metadata_path.open("r", encoding="utf-8") as f:
                        cached_metadata = json.load(f)
                    cache_last_updated = str(
                        cached_metadata.get("document_last_updated") or ""
                    ).strip()
                    cache_usable = bool(
                        current_last_updated
                        and cache_last_updated
                        and current_last_updated == cache_last_updated
                    )
                except Exception:
                    cache_usable = False

            if cache_usable:
                with open(target_cache_path, "r", encoding="utf-8") as f:
                    cached_matrix = json.load(f)
                print(
                    f"[CACHE HIT] Serving revision-matched matrix for wiki URL hash: {url_hash[:16]} "
                    f"last_updated={current_last_updated}"
                )
                await browser.close()
                browser = None
                return {
                    "success": True,
                    "requires_confirmation": False,
                    "filename": page_url,
                    "matrix": cached_matrix,
                    "loaded_from_cache": True,
                    "source_metadata": cached_metadata or source_metadata,
                    "cache_revision_match": True,
                }

            # --------------------------------------------------------
            # FULL DOCUMENT EXTRACTION
            # --------------------------------------------------------
            # We intentionally keep the same browser/page alive so the document
            # isn't opened twice after the metadata gate.
            print(
                f"[DOCUMENT EXTRACTION] Proceeding with full section extraction: "
                f"url_hash={url_hash[:16]} force_refresh={payload.force_refresh}"
            )

            await ensure_full_content_loaded_async(page)
            selector = await _find_content_selector_async(page)
            matrix_rows = await extract_confluence_section_inventory_async(page, selector)

            # Capture actual rendered pixels for image/diagram sections.
            await capture_section_visuals_async(page, context, url_hash[:16], matrix_rows)

            # Re-read metadata after full content loading in case the page header
            # is populated lazily by the Confluence client-side renderer.
            refreshed_metadata = await extract_confluence_source_metadata_async(page, page_url)
            for key, value in refreshed_metadata.items():
                if value:
                    source_metadata[key] = value

            source_metadata["source_content_hash"] = hashlib.sha256(
                json.dumps(matrix_rows, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()

            if not matrix_rows:
                raise HTTPException(
                    status_code=422,
                    detail="No HLD sections were detected in the rendered wiki content.",
                )

            matrix_chunks = []
            for row in matrix_rows:
                content = row.get("content", "")
                audit_tags = HLDAuditChunker()._tag_chunk_focus(content)
                row["audit_tags"] = audit_tags
                row["metadata"] = {
                    "parent_section": row["heading"],
                    "audit_tags": audit_tags,
                    "types": row["types"],
                    "status": row["status"],
                    "level": row["level"],
                    "numbering": row["numbering"],
                    "placeholderCount": row["placeholderCount"],
                    "domId": row["domId"],
                    "visual_evidence": row.get("visual_evidence", []),
                    "visual_review_available": row.get("visual_review_available", False),
                    "visual_review_analyzed": row.get("visual_review_analyzed", False),
                }
                matrix_chunks.append(row)

            # If the visible page metadata changed between the initial lightweight
            # read and the final read, use the final observed value as authoritative.
            if not source_metadata.get("document_last_updated"):
                source_metadata["document_last_updated_source"] = (
                    source_metadata.get("document_last_updated_source")
                    or "unavailable"
                )

            if SERVER_CONFIG.enable_persistence:
                with open(target_cache_path, "w", encoding="utf-8") as f:
                    json.dump(matrix_chunks, f, indent=2)
                with cache_metadata_path.open("w", encoding="utf-8") as f:
                    json.dump(source_metadata, f, indent=2)
                print("[PERSISTENCE] Wiki matrix successfully serialized to disk.")

            await browser.close()
            browser = None

            return {
                "success": True,
                "requires_confirmation": False,
                "filename": page_url,
                "matrix": matrix_chunks,
                "loaded_from_cache": False,
                "source_metadata": source_metadata,
                "cache_revision_match": False,
                "forced_refresh": bool(payload.force_refresh),
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if browser is not None:
            try:
                await browser.close()
            except Exception:
                pass

@app.post("/api/hld/clear-matrix-cache")
def clear_matrix_cache(payload: dict):
    """
    Deletes the saved JSON file for a specific filename, forcing a fresh re-parse.
    """
    filename = payload.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="Missing target filename identifier.")
        
    # Wiki Phase-1 caches are keyed by URL hash; clear the same cache created by generate-matrix.
    target_cache_path = get_wiki_cache_path(filename)
    if os.path.exists(target_cache_path):
        os.remove(target_cache_path)
        metadata_path = Path(str(target_cache_path) + ".meta.json")
        try:
            if metadata_path.exists():
                metadata_path.unlink()
        except OSError:
            pass
        print(f"[CACHE RESET] Cleared wiki matrix cache: {target_cache_path}")
        return {"success": True, "message": "Wiki cache successfully cleared."}
    return {"success": True, "message": "No wiki cache found for this URL."}

def _load_cached_hld_matrix(document_title: str):
    document_id = (document_title or "").strip()
    if document_id.startswith("http://") or document_id.startswith("https://"):
        target_cache_path = get_wiki_cache_path(document_id)
    else:
        target_cache_path = get_file_cache_path(document_id)

    if not os.path.exists(target_cache_path):
        raise HTTPException(status_code=404, detail="No verification matrix found. Please run Phase-1 first.")

    with open(target_cache_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _section_word_count(chunk: dict) -> int:
    return len(str(chunk.get("content") or "").split())


def _choose_hld_auto_tier(
    chunk: dict,
    review_scopes: list[str],
    visual_evidence: list[dict] | None,
) -> tuple[str, str]:
    """Choose an application-level Auto routing preference for one HLD section."""
    metadata = chunk.get("metadata") or {}
    content_types = {str(v).strip().lower() for v in (metadata.get("types") or chunk.get("types") or []) if str(v).strip()}
    scopes = {str(v).strip().lower() for v in (review_scopes or []) if str(v).strip()}
    source_chars = len(str(chunk.get("content") or ""))
    has_visual_attachment = bool(visual_evidence)
    has_visual_content = bool(content_types.intersection({"image", "diagram", "diagram-iframe"}))
    high_risk = bool(scopes.intersection({"security", "vulnerability", "compliance"}))
    architectural = bool(scopes.intersection({"architecture", "integration", "ivr", "reliability", "performance"}))
    text_only = not content_types or content_types.issubset({"text", "table"})
    if has_visual_attachment and high_risk:
        return "intelligence", "attached visual evidence plus high-risk scope"
    if has_visual_attachment and architectural:
        return "intelligence", "attached visual evidence plus architectural/integration/contact-center scope"
    if has_visual_content and high_risk:
        return "intelligence", "visual content plus high-risk scope"
    if has_visual_content:
        return "balance", "visual content detected but no usable visual attachment"
    if high_risk:
        elevated = source_chars > 16000 or len(scopes) >= 3
        return ("intelligence" if elevated else "balance", "high-risk review with elevated complexity" if elevated else "high-risk textual review")
    if architectural:
        return "balance", "standard architecture/integration/IVR-oriented review"
    if text_only and source_chars <= 10000 and len(scopes) <= 2:
        return "efficiency", "compact text/table-only review"
    return "balance", "mixed-content review with moderate complexity"


def _section_matches_scopes(chunk: dict, review_scopes: list[str]) -> bool:
    if not review_scopes:
        return True

    metadata = chunk.get("metadata") or {}
    types = set(metadata.get("types") or chunk.get("types") or [])
    heading = str(metadata.get("parent_section") or chunk.get("heading") or "").lower()
    content = str(chunk.get("content") or "").lower()

    for scope in review_scopes:
        definition = REVIEW_SCOPE_DEFINITIONS.get(scope)
        if not definition:
            continue
        combined = heading + " " + content
        if definition.get("diagram_always") and types.intersection({"diagram", "diagram-iframe", "image"}):
            return True
        if any(keyword in combined for keyword in definition.get("keywords", [])):
            return True
    return False


@app.get("/api/hld/review-scopes")
def get_hld_review_scopes():
    return {
        "success": True,
        "scopes": [
            {"id": key, "label": value["label"]}
            for key, value in REVIEW_SCOPE_DEFINITIONS.items()
        ],
    }


@app.post("/api/hld/review-plan")
def build_hld_review_plan(payload: HLDReviewPlanRequest):
    scopes = _normalise_review_scopes(payload.review_scopes)
    if not scopes:
        raise HTTPException(status_code=400, detail="Select at least one valid HLD review scope.")

    selected_ids = _normalise_section_ids(payload.selected_section_ids)
    matrix_chunks = _load_cached_hld_matrix(payload.document_title)
    eligible_ids = _get_eligible_section_ids(
        payload.document_title,
        scopes,
        selected_ids,
    )
    eligible_set = set(eligible_ids)
    eligible = [c for c in matrix_chunks if int(c.get("id", 0)) in eligible_set]

    total_words = sum(_section_word_count(c) for c in eligible)
    section_count = len(eligible)
    estimated_prompt_tokens = int(round(total_words * 1.35 + section_count * (220 + 35 * len(scopes))))
    estimated_completion_tokens = section_count * max(300, 160 + 70 * max(1, len(scopes)))
    signature = _review_signature(payload.document_title, scopes, eligible_ids)

    return {
        "success": True,
        "document_title": payload.document_title,
        "review_scopes": [
            {"id": s, "label": REVIEW_SCOPE_DEFINITIONS[s]["label"]}
            for s in scopes
        ],
        "selected_section_count": len(selected_ids),
        "eligible_section_ids": eligible_ids,
        "eligible_section_count": section_count,
        "excluded_section_count": (len(selected_ids) - section_count) if selected_ids else (len(matrix_chunks) - section_count),
        "skipped_section_count": len(matrix_chunks) - section_count,
        "total_words": total_words,
        "estimated_prompt_tokens": estimated_prompt_tokens,
        "estimated_completion_tokens": estimated_completion_tokens,
        "estimated_total_tokens": estimated_prompt_tokens + estimated_completion_tokens,
        "estimated_model_calls": section_count,
        "review_signature": signature,
        "review_signature_version": 2,
        "estimate_note": "Planning estimate only. Actual model/SDK usage should be captured during execution.",
    }


def _job_file(job_id: str) -> Path:
    """Legacy compatibility helper; SQLite is now authoritative."""
    return REVIEW_JOB_DIR / f"{job_id}.json"


def _atomic_write_job(job: dict) -> bool:
    try:
        REVIEW_JOB_STORE.upsert_job(job)
        return True
    except Exception as exc:
        print(
            f"[REVIEW JOB WARNING] SQLite persistence failed for job "
            f"{job.get('job_id')}: {exc}"
        )
        return False


def _load_job(job_id: str) -> dict | None:
    try:
        return REVIEW_JOB_STORE.get_job(job_id)
    except Exception as exc:
        print(f"[REVIEW JOB] Failed to load {job_id} from SQLite: {exc}")
        return None


def _find_latest_job_by_review_request(
    document_title: str,
    review_scopes: list[str] | None,
    eligible_section_ids: list[int] | None,
) -> dict | None:
    try:
        signature = _review_signature(
            document_title,
            _normalise_review_scopes(review_scopes),
            _normalise_section_ids(eligible_section_ids),
        )
        return REVIEW_JOB_STORE.find_latest(
            document_url=document_title,
            review_signature=signature,
        )
    except Exception as exc:
        print(f"[REVIEW JOB] SQLite lookup failed: {exc}")
        return None


def _job_public_view(job: dict | None) -> dict | None:
    if not job:
        return None
    return {
        "job_id": job.get("job_id"),
        "document_title": job.get("document_title"),
        "document_url": job.get("document_url") or job.get("document_title"),
        "source_version": job.get("source_version"),
        "source_version_timestamp": job.get("source_version_timestamp"),
        "source_version_source": job.get("source_version_source"),
        "document_last_updated": job.get("document_last_updated"),
        "document_last_updated_by": job.get("document_last_updated_by"),
        "document_created_by": job.get("document_created_by"),
        "document_last_updated_source": job.get("document_last_updated_source"),
        "source_content_hash": job.get("source_content_hash"),
        "review_type": job.get("review_type") or "Technical Document Review",
        "review_scopes": job.get("review_scopes", []),
        "selected_section_ids": job.get("selected_section_ids", []),
        "eligible_section_ids": job.get("eligible_section_ids", []),
        "selected_section_count": len(job.get("selected_section_ids", []) or []),
        "eligible_section_count": len(job.get("eligible_section_ids", []) or []),
        "excluded_section_count": max(0, len(job.get("selected_section_ids", []) or []) - len(job.get("eligible_section_ids", []) or [])),
        "status": job.get("status", "UNKNOWN"),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "updated_at": job.get("updated_at"),
        "duration_ms": job.get("duration_ms", 0),
        "duration_seconds": round(float(job.get("duration_ms", 0) or 0) / 1000.0, 3),
        "finding_count": int(job.get("finding_count", 0) or 0),
        "pass_count": int(job.get("pass_count", 0) or 0),
        "manual_review_count": int(job.get("manual_review_count", 0) or 0),
        "input_tokens": int(job.get("input_tokens", 0) or 0),
        "output_tokens": int(job.get("output_tokens", 0) or 0),
        "reasoning_tokens": int(job.get("reasoning_tokens", 0) or 0),
        "ai_credits": float(job.get("ai_credits", 0) or 0),
        "model_calls": int(job.get("model_calls", 0) or 0),
        "actual_models": job.get("actual_models", []),
        "auto_tiers": job.get("auto_tiers", []),
        "progress": job.get("progress", {}),
        "usage": job.get("usage", {}),
        "review_plan": job.get("review_plan", {}),
        "review_errors": job.get("review_errors", []),
        "error": job.get("error"),
        "recovery_note": job.get("recovery_note"),
        "result": job.get("result"),
    }


def _mark_recoverable_jobs_on_startup() -> None:
    # A process restart cannot safely continue an in-flight Copilot session.
    # Completed section results are preserved so a later start can resume only what remains.
    try:
        jobs, _ = REVIEW_JOB_STORE.list_jobs(limit=500, offset=0)
        for job in jobs:
            if job.get("status") in {"QUEUED", "RUNNING", "CANCEL_REQUESTED"}:
                job["status"] = "RECOVERY_REQUIRED"
                job["recovery_note"] = (
                    "Server restarted while review was active. Completed sections are preserved; "
                    "restarting the same review resumes only remaining sections."
                )
                _atomic_write_job(job)
    except Exception as exc:
        print(f"[REVIEW JOB] Startup recovery scan failed: {exc}")

_mark_recoverable_jobs_on_startup()


def _job_section_progress_callback(job_id: str, section_id: int, heading: str, section_status: str, aggregate: dict, eligible_ids: list[int]) -> None:
    job = _load_job(job_id) or {"job_id": job_id}
    progress = job.setdefault("progress", {})
    completed = {int(x) for x in progress.get("completed_section_ids", [])}
    if section_status == "COMPLETED":
        completed.add(int(section_id))
    progress.update({
        "total_sections": len(eligible_ids),
        "completed_sections": len(completed),
        "completed_section_ids": sorted(completed),
        "remaining_sections": max(0, len(eligible_ids) - len(completed)),
        "current_section_id": int(section_id),
        "current_section_heading": heading,
        "last_section_status": section_status,
        "stage": "RUNNING",
    })
    job["result"] = {"success": True, "segmented_blueprint": aggregate}
    job["usage"] = (aggregate.get("ai_consumption") or {}).get("totals") or {}
    job["review_errors"] = aggregate.get("review_errors", [])
    _atomic_write_job(job)


def _run_review_job_worker(job_id: str) -> None:
    cancel_event = REVIEW_CANCEL_EVENTS.setdefault(job_id, threading.Event())
    job = _load_job(job_id)
    if not job:
        return
    payload = HLDIngestionRequest(
        document_title=job["document_title"],
        raw_content="",
        project_scope=job.get("project_scope", "IVR Context Validation"),
        review_scopes=job.get("review_scopes", []),
        selected_section_ids=job.get("eligible_section_ids", []),
    )
    try:
        completed = {int(x) for x in job.get("progress", {}).get("completed_section_ids", [])}
        initial_result = None
        stored_result = job.get("result") or {}
        if isinstance(stored_result, dict) and isinstance(stored_result.get("segmented_blueprint"), dict):
            initial_result = stored_result["segmented_blueprint"]
        job["status"] = "RUNNING"
        job["started_at"] = job.get("started_at") or datetime.utcnow().isoformat(timespec="seconds") + "Z"
        job.setdefault("progress", {})["stage"] = "RUNNING"
        _atomic_write_job(job)

        result = _run_hld_review_core(
            payload,
            progress_callback=lambda sid, heading, status, aggregate: _job_section_progress_callback(
                job_id, sid, heading, status, aggregate, job.get("eligible_section_ids", [])
            ),
            cancel_event=cancel_event,
            resume_completed_ids=completed,
            initial_result=initial_result,
        )

        final_job = _load_job(job_id) or job
        final_job["result"] = {"success": True, "segmented_blueprint": result}
        final_job["usage"] = (result.get("ai_consumption") or {}).get("totals") or {}
        final_job["review_errors"] = result.get("review_errors", [])
        usage_totals = result.get("ai_consumption", {}).get("totals") or {}
        final_job["input_tokens"] = int(usage_totals.get("input_tokens", 0) or 0)
        final_job["output_tokens"] = int(usage_totals.get("output_tokens", 0) or 0)
        final_job["reasoning_tokens"] = int(usage_totals.get("reasoning_tokens", 0) or 0)
        final_job["ai_credits"] = float(usage_totals.get("ai_credits_from_nano_aiu", usage_totals.get("ai_credits", 0)) or 0)
        final_job["model_calls"] = int(usage_totals.get("model_calls", 0) or 0)
        final_job["finding_count"] = len(result.get("findings", []) or [])
        final_job["pass_count"] = len(result.get("passed_checks", []) or [])
        final_job["manual_review_count"] = len(result.get("manual_review", []) or [])
        final_job["actual_models"] = sorted({
            str(item.get("model")).strip()
            for item in (result.get("ai_consumption", {}).get("by_section") or [])
            for _ in [0]
            if item.get("model")
        } | {
            str(model).strip()
            for item in (result.get("ai_consumption", {}).get("by_section") or [])
            for model in (item.get("models") or [])
            if str(model).strip()
        })
        final_job["auto_tiers"] = sorted({
            str(item.get("routing", {}).get("requestedAutoTier")).strip()
            for item in (result.get("ai_consumption", {}).get("by_section") or [])
            if item.get("routing", {}).get("requestedAutoTier")
        })
        started = final_job.get("started_at")
        completed_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        final_job["completed_at"] = completed_at
        if started:
            try:
                start_dt = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
                final_job["duration_ms"] = max(0, int((end_dt - start_dt).total_seconds() * 1000))
            except Exception:
                pass

        if cancel_event.is_set():
            final_job["status"] = "CANCELLED"
            final_job["recovery_note"] = "Review stopped by user. Completed sections are preserved and can be resumed by starting the same review again."
        elif final_job.get("progress", {}).get("completed_sections", 0) >= final_job.get("progress", {}).get("total_sections", 0):
            final_job["status"] = "COMPLETED"
        else:
            final_job["status"] = "FAILED"
        final_job.setdefault("progress", {})["stage"] = final_job["status"]
        _atomic_write_job(final_job)
    except Exception as exc:
        traceback.print_exc()
        final_job = _load_job(job_id) or job
        final_job["status"] = "FAILED"
        final_job["error"] = str(exc)
        final_job.setdefault("progress", {})["stage"] = "FAILED"
        _atomic_write_job(final_job)
    finally:
        REVIEW_CANCEL_EVENTS.pop(job_id, None)


def _start_or_resume_review_job(request: HLDReviewStartRequest) -> dict:
    scopes = _normalise_review_scopes(request.review_scopes)
    if not scopes:
        raise HTTPException(status_code=400, detail="Select at least one valid HLD review scope.")

    selected_ids = _normalise_section_ids(request.selected_section_ids)
    eligible_ids = _get_eligible_section_ids(
        request.document_title,
        scopes,
        selected_ids,
    )

    if not eligible_ids:
        raise HTTPException(
            status_code=400,
            detail="The current section selection and review scopes produced no reviewable sections.",
        )

    signature = _review_signature(
        request.document_title,
        scopes,
        eligible_ids,
    )

    existing = _find_latest_job_by_review_request(
        request.document_title,
        scopes,
        eligible_ids,
    )

    if existing and existing.get("status") in {"RUNNING", "QUEUED", "CANCEL_REQUESTED"}:
        return _job_public_view(existing)

    if existing and existing.get("status") == "COMPLETED" and not request.force_new_review:
        return _job_public_view(existing)

    existing_completed = {
        int(x)
        for x in (existing or {}).get("progress", {}).get("completed_section_ids", [])
    }
    can_resume_partial = (
        existing
        and existing.get("status") in {"RECOVERY_REQUIRED", "FAILED", "CANCELLED"}
        and len(existing_completed) < len(eligible_ids)
    )

    if can_resume_partial:
        job = existing
        job["status"] = "QUEUED"
        job["error"] = None
        job["recovery_note"] = None
        job["review_signature"] = signature
        job["review_signature_version"] = 2
        job["document_title"] = request.document_title
        job["document_url"] = request.document_title
        job["document_last_updated"] = request.document_last_updated
        job["document_last_updated_by"] = request.document_last_updated_by
        job["document_created_by"] = request.document_created_by
        job["document_last_updated_source"] = (
            request.document_last_updated_source
            or ("confluence_page_header" if request.document_last_updated else None)
        )
        job["review_scopes"] = scopes
        job["selected_section_ids"] = selected_ids
        job["eligible_section_ids"] = eligible_ids
        job["review_plan"] = request.review_plan or job.get("review_plan") or {}
        _atomic_write_job(job)
    else:
        job_id = hashlib.sha256(
            f"{signature}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:24]
        job = {
            "job_id": job_id,
            "review_signature": signature,
            "review_signature_version": 2,
            "document_title": request.document_title,
            "document_url": request.document_title,
            "source_version": request.source_version,
            "source_version_timestamp": request.source_version_timestamp,
            "source_version_source": request.source_version_source,
            "document_last_updated": request.document_last_updated,
            "document_last_updated_by": request.document_last_updated_by,
            "document_created_by": request.document_created_by,
            "document_last_updated_source": request.document_last_updated_source
            or ("confluence_page_header" if request.document_last_updated else None),
            "source_content_hash": request.source_content_hash,
            "review_type": request.review_type or "Technical Document Review",
            "review_scopes": scopes,
            "selected_section_ids": selected_ids,
            "eligible_section_ids": eligible_ids,
            "project_scope": request.project_scope or "IVR Context Validation",
            "status": "QUEUED",
            "created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "started_at": None,
            "updated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "progress": {
                "total_sections": len(eligible_ids),
                "completed_sections": 0,
                "completed_section_ids": [],
                "remaining_sections": len(eligible_ids),
                "current_section_id": None,
                "current_section_heading": None,
                "last_section_status": None,
                "stage": "QUEUED",
            },
            "usage": {},
            "review_errors": [],
            "result": None,
            "review_plan": request.review_plan or {},
        }
        _atomic_write_job(job)

    job_id = job["job_id"]
    REVIEW_EXECUTOR.submit(_run_review_job_worker, job_id)
    return _job_public_view(job)


@app.post("/api/hld/review/start")
def start_hld_review(payload: HLDReviewStartRequest):
    """Start a new review or resume/recover an existing matching review job."""
    job = _start_or_resume_review_job(payload)
    return {"success": True, "job": job}


@app.get("/api/hld/jobs")
def list_review_jobs(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    document_url: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    jobs, total = REVIEW_JOB_STORE.list_jobs(
        status=status,
        search=search,
        document_url=document_url,
        limit=limit,
        offset=offset,
    )
    return {
        "success": True,
        "jobs": [_job_public_view(job) for job in jobs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/hld/jobs/{job_id}")
def get_review_job_detail(job_id: str):
    job = _load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Review job not found.")
    return {"success": True, "job": _job_public_view(job)}


@app.delete("/api/hld/jobs/completed")
def clear_completed_review_jobs(payload: dict | None = None):
    payload = payload or {}
    job_ids = payload.get("job_ids")
    if job_ids is not None and not isinstance(job_ids, list):
        raise HTTPException(status_code=400, detail="job_ids must be an array when provided.")
    deleted = REVIEW_JOB_STORE.delete_completed(job_ids)
    return {"success": True, "deleted_count": deleted}


@app.delete("/api/hld/jobs/{job_id}")
def delete_review_job(job_id: str):
    job = _load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Review job not found.")
    if job.get("status") in ACTIVE_REVIEW_STATUSES:
        raise HTTPException(status_code=409, detail="Active review jobs must be cancelled before deletion.")
    deleted = REVIEW_JOB_STORE.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=409, detail="Only Completed, Failed, or Cancelled jobs can be deleted.")
    return {"success": True, "job_id": job_id}


@app.get("/api/hld/review/{job_id}")
def get_hld_review_job(job_id: str):
    job = _load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="HLD review job not found.")
    return {"success": True, "job": _job_public_view(job)}


@app.post("/api/hld/review/{job_id}/cancel")
def cancel_hld_review(job_id: str):
    job = _load_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="HLD review job not found.")
    if job.get("status") in {"COMPLETED", "FAILED", "CANCELLED"}:
        return {"success": True, "job": _job_public_view(job)}
    job["status"] = "CANCEL_REQUESTED"
    job.setdefault("progress", {})["stage"] = "CANCEL_REQUESTED"
    _atomic_write_job(job)
    event = REVIEW_CANCEL_EVENTS.setdefault(job_id, threading.Event())
    event.set()
    return {"success": True, "job": _job_public_view(job)}


def _run_hld_review_core(
    payload: HLDIngestionRequest,
    progress_callback=None,
    cancel_event: threading.Event | None = None,
    resume_completed_ids: set[int] | None = None,
    initial_result: dict | None = None,
):
    """
    Phase 2: Review each selected HLD section exactly once with one Copilot turn.

    The selected review scopes are supplied together in that one turn. This keeps the
    review stable and avoids multiplying model calls. Exact SDK usage is therefore
    attributable to the section, while scope-level token cost is reported as shared
    across the scopes selected for that section rather than being falsely divided.
    """
    print(f"[HLD AUDIT] Loading cached matrix for: {payload.document_title}")
    matrix_chunks = _load_cached_hld_matrix(payload.document_title)

    review_scopes = [s for s in payload.review_scopes if s in REVIEW_SCOPE_DEFINITIONS]
    selected_ids = {int(x) for x in payload.selected_section_ids}

    filtered_chunks = []
    for chunk in matrix_chunks:
        section_id = int(chunk.get("id", 0))
        if selected_ids and section_id not in selected_ids:
            continue
        if not _section_matches_scopes(chunk, review_scopes):
            continue
        if ((chunk.get("metadata") or {}).get("status") or chunk.get("status")) == "empty":
            continue
        filtered_chunks.append(chunk)

    matrix_chunks = filtered_chunks
    print(f"[HLD AUDIT] Review scopes={review_scopes or ['ALL']} sections={len(matrix_chunks)}")

    aggregated_blueprint = json.loads(json.dumps(initial_result)) if isinstance(initial_result, dict) else {
        "document_metadata": {
            "title": payload.document_title,
            "segments_found": 0,
            "review_scopes": review_scopes or ["ALL"],
            "sections_reviewed": len(matrix_chunks),
        },
        "review_summary": {
            "overall_status": "PASS",
            "finding_count": 0,
            "pass_count": 0,
            "manual_review_count": 0,
            "review_error_count": 0,
            "visual_sections_reviewed": 0,
        },
        "findings": [],
        "passed_checks": [],
        "manual_review": [],
        "review_errors": [],
        "review_required_sections": [],
        "ivr_flow_requirements": [],
        "ai_consumption": {
            "attribution_mode": "exact-by-section-shared-across-selected-scopes",
            "note": "SDK usage is exact for each section/turn. A single combined turn covers all selected scopes, so tokens and credits are not artificially split between scopes.",
            "by_section": [],
            "by_scope": {},
            "by_model": {},
            "by_auto_tier": {},
            "totals": {
                "model_calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "reasoning_tokens": 0,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
                "duration_ms": 0,
                "total_nano_aiu": 0,
                "ai_credits_from_nano_aiu": 0.0,
                "premium_request_cost": 0,
            },
        },
    }

    aggregated_blueprint.setdefault("findings", [])
    aggregated_blueprint.setdefault("passed_checks", [])
    aggregated_blueprint.setdefault("manual_review", [])
    aggregated_blueprint.setdefault("review_errors", [])
    aggregated_blueprint.setdefault("review_required_sections", [])
    aggregated_blueprint.setdefault("ivr_flow_requirements", [])
    aggregated_blueprint.setdefault("ai_consumption", {
        "attribution_mode": "exact-by-section-shared-across-selected-scopes",
        "note": "SDK usage is exact for each section/turn. A single combined turn covers all selected scopes, so tokens and credits are not artificially split between scopes.",
        "by_section": [], "by_scope": {}, "by_model": {}, "by_auto_tier": {},
        "totals": {"model_calls": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "reasoning_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0, "duration_ms": 0, "total_nano_aiu": 0, "ai_credits_from_nano_aiu": 0.0, "premium_request_cost": 0}
    })
    resume_completed_ids = set(resume_completed_ids or set())

    def add_usage_record(usage: dict, section_id: int, section_heading: str, scopes: list[str]):
        if not isinstance(usage, dict):
            return

        usage_item = dict(usage)
        usage_item["sectionId"] = section_id
        usage_item["sectionHeading"] = section_heading
        usage_item["reviewScopes"] = list(scopes)
        usage_item["attributionMode"] = "shared-section-call"
        aggregated_blueprint["ai_consumption"]["by_section"].append(usage_item)

        routing = usage_item.get("routing") or {}
        requested_tier = routing.get("requestedAutoTier") or "default"
        actual_model = routing.get("actualModel") or ((usage_item.get("models") or [None])[0])
        usage_item["routing"] = {
            "requestedModelMode": routing.get("requestedModelMode") or "auto",
            "requestedAutoTier": requested_tier if requested_tier != "default" else None,
            "selectionReason": routing.get("selectionReason"),
            "actualModel": actual_model,
            "actualAutoTier": routing.get("actualAutoTier"),
            "pendingAutoTier": routing.get("pendingAutoTier"),
            "activatingAutoTier": routing.get("activatingAutoTier"),
            "visualRequired": bool(routing.get("visualRequired")),
            "modelChangeEvents": routing.get("modelChangeEvents") or [],
        }

        totals = aggregated_blueprint["ai_consumption"]["totals"]
        mapping = (
            ("modelCalls", "model_calls"),
            ("inputTokens", "input_tokens"),
            ("outputTokens", "output_tokens"),
            ("totalTokens", "total_tokens"),
            ("reasoningTokens", "reasoning_tokens"),
            ("cacheReadTokens", "cache_read_tokens"),
            ("cacheWriteTokens", "cache_write_tokens"),
            ("durationMs", "duration_ms"),
            ("totalNanoAiu", "total_nano_aiu"),
            ("aiCreditsFromNanoAiu", "ai_credits_from_nano_aiu"),
            ("premiumRequestCost", "premium_request_cost"),
        )
        for source_key, target_key in mapping:
            try:
                totals[target_key] += usage_item.get(source_key, 0) or 0
            except (TypeError, ValueError):
                pass

        # Per-model usage remains exact because modelMetrics is tied to this one section turn.
        for model, model_data in (usage_item.get("modelBreakdown") or {}).items():
            bucket = aggregated_blueprint["ai_consumption"]["by_model"].setdefault(
                model,
                {
                    "calls": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_tokens": 0,
                    "total_nano_aiu": 0,
                    "ai_credits_from_nano_aiu": 0.0,
                },
            )
            bucket["calls"] += int(model_data.get("calls") or 0)
            bucket["input_tokens"] += int(model_data.get("inputTokens") or 0)
            bucket["output_tokens"] += int(model_data.get("outputTokens") or 0)
            bucket["reasoning_tokens"] += int(model_data.get("reasoningTokens") or 0)
            bucket["total_nano_aiu"] += int(model_data.get("totalNanoAiu") or 0)
            bucket["ai_credits_from_nano_aiu"] += float(model_data.get("aiCreditsFromNanoAiu") or 0)

        tier_key = requested_tier
        tier_bucket = aggregated_blueprint["ai_consumption"]["by_auto_tier"].setdefault(
            tier_key,
            {"sections_reviewed": 0, "model_calls": 0, "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0, "ai_credits": 0.0, "actual_models": []}
        )
        tier_bucket["sections_reviewed"] += 1
        tier_bucket["model_calls"] += int(usage_item.get("modelCalls") or 0)
        tier_bucket["input_tokens"] += int(usage_item.get("inputTokens") or 0)
        tier_bucket["output_tokens"] += int(usage_item.get("outputTokens") or 0)
        tier_bucket["reasoning_tokens"] += int(usage_item.get("reasoningTokens") or 0)
        tier_bucket["ai_credits"] += float(usage_item.get("aiCreditsFromNanoAiu") or 0)
        if actual_model and actual_model not in tier_bucket["actual_models"]:
            tier_bucket["actual_models"].append(actual_model)

        for scope in scopes:
            bucket = aggregated_blueprint["ai_consumption"]["by_scope"].setdefault(
                scope,
                {
                    "sections_reviewed": 0,
                    "shared_model_calls": 0,
                    "usage_attribution": "shared-section-call",
                },
            )
            bucket["sections_reviewed"] += 1
            bucket["shared_model_calls"] += int(usage_item.get("modelCalls") or 0)

    try:
        proc = get_live_copilot_process()

        for idx, chunk in enumerate(matrix_chunks):
            section_id = int(chunk.get("id", idx + 1))
            if section_id in resume_completed_ids:
                continue
            if cancel_event is not None and cancel_event.is_set():
                print(f"[HLD AUDIT] Cancellation requested before section {section_id}; stopping queue.")
                break
            metadata = chunk.get("metadata") or {}
            header_context = metadata.get("parent_section") or chunk.get("heading") or f"Section {chunk.get('id', idx + 1)}"
            visual_evidence = chunk.get("visual_evidence") or metadata.get("visual_evidence") or []
            visual_scopes = {"architecture", "security", "vulnerability", "integration", "ivr", "documentation", "reliability", "performance"}
            should_attach_visuals = bool(visual_evidence) and bool(set(review_scopes).intersection(visual_scopes))
            content_types = metadata.get("types") or chunk.get("types") or []
            selected_scopes = review_scopes or ["architecture"]
            requested_auto_tier, requested_auto_tier_reason = _choose_hld_auto_tier(
                chunk, selected_scopes, visual_evidence if should_attach_visuals else []
            )

            print(
                f"   ↳ Reviewing section {idx+1}/{len(matrix_chunks)}: [{header_context}] "
                f"scopes={','.join(selected_scopes)} autoTier={requested_auto_tier} "
                f"reason={requested_auto_tier_reason}"
            )
            if progress_callback:
                progress_callback(section_id, header_context, "STARTED", aggregated_blueprint)

            script_payload = {
                "relativePath": f"{payload.document_title} -> {header_context}",
                "source": chunk.get("content", ""),
                "diagramType": "HLD_SEGMENTATION_MODE",
                "reviewScopes": selected_scopes,
                "contentTypes": content_types,
                "sectionId": section_id,
                "sectionHeading": header_context,
                "visualReviewRequired": should_attach_visuals,
                "visualEvidence": visual_evidence if should_attach_visuals else [],
                # The Node daemon owns Auto routing. These fields make the contract explicit
                # and allow future routing-policy versioning without selecting a concrete model here.
                "modelMode": "auto",
                "routingPolicy": "hld-auto-router-v2",
                "requestedAutoTier": requested_auto_tier,
                "requestedAutoTierReason": requested_auto_tier_reason,
            }

            proc.stdin.write(json.dumps(script_payload) + "\n")
            proc.stdin.flush()

            stdout_line = proc.stdout.readline()
            if not stdout_line:
                stderr_preview = ""
                try:
                    if proc.poll() is not None:
                        stderr_preview = f" Copilot daemon exited with code {proc.returncode}."
                except Exception:
                    pass
                raise Exception(f"Copilot background daemon disconnected.{stderr_preview}")

            response_data = json.loads(stdout_line.strip())
            print(f"[HLD REVIEW DEBUG] Node response keys: {list(response_data.keys())}")

            if not response_data.get("success"):
                print(
                    f"[HLD REVIEW ERROR] Node reviewer returned failure: "
                    f"section={section_id} error={response_data.get('error')}"
                )
                # Preserve any usage telemetry emitted before the failure.
                add_usage_record(response_data.get("usage"), section_id, header_context, selected_scopes)
                aggregated_blueprint["review_errors"].append({
                    "section_id": section_id,
                    "section": header_context,
                    "error": response_data.get("error", "Unknown Copilot review failure"),
                    "raw_response": response_data.get("raw_response"),
                })
                if progress_callback:
                    progress_callback(section_id, header_context, "FAILED", aggregated_blueprint)
                continue

            add_usage_record(response_data.get("usage"), section_id, header_context, selected_scopes)

            raw_payload = response_data.get("mermaid_string")
            if isinstance(raw_payload, dict):
                chunk_blueprint = raw_payload
            elif isinstance(raw_payload, str):
                raw_json_str = raw_payload.strip()
                raw_json_str = re.sub(r'^```(?:json)?\s*', '', raw_json_str, flags=re.IGNORECASE)
                raw_json_str = re.sub(r'\s*```$', '', raw_json_str).strip()
                try:
                    chunk_blueprint = json.loads(raw_json_str)
                except json.JSONDecodeError as parse_error:
                    print(f"[HLD REVIEW ERROR] JSON parse failed for [{header_context}]: {parse_error}")
                    print(f"[HLD REVIEW DEBUG] Raw payload preview: {raw_json_str[:2000]}")
                    continue
            else:
                print(f"[HLD REVIEW ERROR] Unexpected mermaid_string type: {type(raw_payload).__name__}")
                continue

            findings = chunk_blueprint.get("findings", [])
            passes = chunk_blueprint.get("passed_checks", [])
            manual = chunk_blueprint.get("manual_review", [])
            print(
                f"[HLD REVIEW DEBUG] Parsed section [{header_context}] -> "
                f"findings={len(findings) if isinstance(findings, list) else 0}, "
                f"passes={len(passes) if isinstance(passes, list) else 0}, "
                f"manual={len(manual) if isinstance(manual, list) else 0}"
            )

            for key in ("findings", "passed_checks", "manual_review", "review_required_sections", "ivr_flow_requirements"):
                values = chunk_blueprint.get(key)
                if isinstance(values, list):
                    aggregated_blueprint[key].extend(values)

            if should_attach_visuals:
                aggregated_blueprint["review_summary"]["visual_sections_reviewed"] += 1

            if progress_callback:
                progress_callback(section_id, header_context, "COMPLETED", aggregated_blueprint)

        finding_count = len(aggregated_blueprint["findings"])
        pass_count = len(aggregated_blueprint["passed_checks"])
        manual_count = len(aggregated_blueprint["manual_review"])
        review_error_count = len(aggregated_blueprint["review_errors"])
        if finding_count:
            overall_status = "FINDINGS"
        elif manual_count:
            overall_status = "MANUAL_REVIEW"
        elif review_error_count:
            overall_status = "REVIEW_INCOMPLETE"
        else:
            overall_status = "PASS"
        aggregated_blueprint["review_summary"].update({
            "overall_status": overall_status,
            "finding_count": finding_count,
            "pass_count": pass_count,
            "manual_review_count": manual_count,
            "review_error_count": review_error_count,
        })
        total_segments = finding_count + pass_count + manual_count
        aggregated_blueprint["document_metadata"]["segments_found"] = total_segments

        print(
            "[HLD REVIEW FINAL] "
            f"findings={finding_count}, passed={pass_count}, manual={manual_count}, "
            f"status={overall_status}, model_calls={aggregated_blueprint['ai_consumption']['totals']['model_calls']}, "
            f"review_errors={review_error_count}, "
            f"auto_tiers={list(aggregated_blueprint['ai_consumption']['by_auto_tier'].keys())}"
        )

        return aggregated_blueprint
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/hld/ingest")
def ingest_and_segment_hld(payload: HLDIngestionRequest):
    """Compatibility endpoint for callers that still expect a synchronous review."""
    result = _run_hld_review_core(payload)
    return {"success": True, "document_title": payload.document_title, "segmented_blueprint": result}


def _safe_report_filename(document_title: str) -> str:
    base = str(document_title or "HLD_Review").split("#", 1)[0]
    base = os.path.basename(base).strip() or "HLD_Review"
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    return f"{base}_HLD_Review.xlsx"


def _excel_text(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def _format_excel_sheet(ws, widths=None, freeze="A2"):
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    ws.sheet_view.showGridLines = False
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2A5B8C")
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 28
    thin = Side(style="thin", color="D9E0E7")
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.border = Border(bottom=thin)
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    ws.freeze_panes = freeze
    if widths:
        for idx, width in widths.items():
            ws.column_dimensions[get_column_letter(idx)].width = width


def _write_sheet(ws, headers, rows):
    ws.append(headers)
    for row in rows:
        ws.append([_excel_text(v) for v in row])
    if headers:
        ws.auto_filter.ref = f"A1:{chr(64 + min(len(headers), 26))}{max(1, ws.max_row)}"


@app.post("/api/hld/export-excel")
def export_hld_review_excel(payload: HLDExcelExportRequest):
    """Create a polished multi-sheet Excel report from a completed HLD review."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        result = payload.review_result or {}
        metadata = result.get("document_metadata") or {}
        summary = result.get("review_summary") or {}
        findings = result.get("findings") or []
        passes = result.get("passed_checks") or []
        manual = result.get("manual_review") or []
        errors = result.get("review_errors") or []
        consumption = result.get("ai_consumption") or {}
        totals = consumption.get("totals") or {}
        by_section = consumption.get("by_section") or []
        by_scope = consumption.get("by_scope") or {}
        by_model = consumption.get("by_model") or {}

        wb = Workbook()
        summary_ws = wb.active
        summary_ws.title = "Executive Summary"
        summary_ws.sheet_view.showGridLines = False
        summary_ws.merge_cells("A1:F1")
        summary_ws["A1"] = "IVR SDLC Automated Analyst Platform - HLD Review"
        summary_ws["A1"].font = Font(size=18, bold=True, color="FFFFFF")
        summary_ws["A1"].fill = PatternFill("solid", fgColor="16324F")
        summary_ws["A3"] = "Document"
        summary_ws["B3"] = metadata.get("title") or payload.document_title
        summary_ws["A4"] = "Review status"
        summary_ws["B4"] = summary.get("overall_status") or ""
        summary_ws["A5"] = "Sections reviewed"
        summary_ws["B5"] = metadata.get("sections_reviewed", 0)
        summary_ws["A6"] = "Findings"
        summary_ws["B6"] = "=COUNTA(Findings!A:A)-1"
        summary_ws["A7"] = "Passed checks"
        summary_ws["B7"] = "=COUNTA('Passed Checks'!A:A)-1"
        summary_ws["A8"] = "Manual review"
        summary_ws["B8"] = "=COUNTA('Manual Review'!A:A)-1"
        summary_ws["A9"] = "Review errors"
        summary_ws["B9"] = "=COUNTA('Review Errors'!A:A)-1"
        summary_ws["A11"] = "Actual model calls"
        summary_ws["B11"] = totals.get("model_calls", 0)
        summary_ws["A12"] = "Actual input tokens"
        summary_ws["B12"] = totals.get("input_tokens", 0)
        summary_ws["A13"] = "Actual output tokens"
        summary_ws["B13"] = totals.get("output_tokens", 0)
        summary_ws["A14"] = "Actual reasoning tokens"
        summary_ws["B14"] = totals.get("reasoning_tokens", 0)
        summary_ws["A15"] = "SDK AI credits"
        summary_ws["B15"] = totals.get("ai_credits_from_nano_aiu", 0)
        for r in list(range(3,10)) + list(range(11,16)):
            summary_ws[f"A{r}"].font = Font(bold=True, color="4A5A6B")
            summary_ws[f"A{r}"].fill = PatternFill("solid", fgColor="EEF1F4")
            summary_ws[f"B{r}"].alignment = Alignment(vertical="top", wrap_text=True)
        summary_ws["B15"].number_format = "0.000000"
        for c,w in {1:28,2:78,3:18,4:18,5:18,6:18}.items():
            summary_ws.column_dimensions[get_column_letter(c)].width=w

        fws = wb.create_sheet("Findings")
        _write_sheet(fws,
            ["Finding ID","Scope","Category","Severity","Title","Finding","Evidence - Text","Evidence - Visual","Impact","Recommendation","Confidence","Section Reference","Visual Reviewed"],
            [[f.get("finding_id"),f.get("scope"),f.get("category"),f.get("severity"),f.get("title"),f.get("finding"),(f.get("evidence") or {}).get("text"),(f.get("evidence") or {}).get("visual_observation"),f.get("impact"),f.get("recommendation"),f.get("confidence"),f.get("section_reference"),"Yes" if f.get("visual_reviewed") else "No"] for f in findings])
        _format_excel_sheet(fws,{1:14,2:16,3:22,4:13,5:40,6:60,7:45,8:55,9:50,10:55,11:12,12:60,13:15})
        sev_fill={"Critical":"F4CCCC","High":"FCE4D6","Medium":"FBEAD9","Low":"FFF2CC","Informational":"EDEDED"}
        for row in range(2,fws.max_row+1):
            fill=sev_fill.get(str(fws.cell(row,4).value))
            if fill: fws.cell(row,4).fill=PatternFill("solid",fgColor=fill)

        pws=wb.create_sheet("Passed Checks")
        _write_sheet(pws,["Scope","Category","Check","Evidence","Section Reference","Visual Reviewed"],[[p.get("scope"),p.get("category"),p.get("check"),p.get("evidence"),p.get("section_reference"),"Yes" if p.get("visual_reviewed") else "No"] for p in passes])
        _format_excel_sheet(pws,{1:18,2:22,3:60,4:75,5:60,6:16})

        mws=wb.create_sheet("Manual Review")
        _write_sheet(mws,["Scope","Reason","Required Action","Section Reference"],[[m.get("scope"),m.get("reason"),m.get("required_action"),m.get("section_reference")] for m in manual])
        _format_excel_sheet(mws,{1:18,2:80,3:80,4:65})

        ews=wb.create_sheet("Review Errors")
        _write_sheet(ews,["Section ID","Section","Error","Raw Response"],[[e.get("section_id"),e.get("section"),e.get("error"),e.get("raw_response")] for e in errors])
        _format_excel_sheet(ews,{1:12,2:50,3:85,4:80})

        tws=wb.create_sheet("AI Telemetry")
        trows=[]
        for u in by_section:
            d=u.get("diagnostics") or {}
            ci=u.get("contextInfo") or {}
            routing = u.get("routing") or {}
            trows.append([
                u.get("sectionId"),u.get("sectionHeading"),", ".join(u.get("reviewScopes") or []),
                routing.get("requestedModelMode") or "auto", routing.get("requestedAutoTier") or "default",
                routing.get("selectionReason") or "", routing.get("actualModel") or (", ".join(u.get("models") or [])),
                routing.get("actualAutoTier") or "",
                u.get("modelCalls",0),u.get("inputTokens",0),u.get("outputTokens",0),u.get("reasoningTokens",0),u.get("totalTokens",0),
                u.get("aiCreditsFromNanoAiu",0),u.get("premiumRequestCost",0),"Yes" if u.get("visualReviewed") else "No",u.get("turnStatus"),
                d.get("sourceChars",0),d.get("sourceEstimatedTokens",0),d.get("promptChars",0),d.get("promptEstimatedTokens",0),
                d.get("systemPromptChars",0),d.get("attachmentCount",0),ci.get("totalTokens",0),ci.get("promptTokenLimit",0),
                ci.get("systemTokens",0),ci.get("conversationTokens",0),ci.get("toolDefinitionsTokens",0)
            ])
        _write_sheet(tws,["Section ID","Section","Scopes","Requested Mode","Requested Auto Tier","Selection Reason","Actual Model","Actual Auto Tier","Calls","Input Tokens","Output Tokens","Reasoning Tokens","Total Tokens","AI Credits","Premium Request Cost","Visual Reviewed","Turn Status","Source Chars","Source Est. Tokens","Prompt Chars","Prompt Est. Tokens","System Chars","Attachments","Context Tokens","Context Limit","Context System","Context Conversation","Context Tools"],trows)
        _format_excel_sheet(tws,{1:12,2:42,3:34,4:16,5:18,6:55,7:26,8:18,9:10,10:14,11:15,12:17,13:14,14:14,15:20,16:16,17:14,18:14,19:16,20:14,21:16,22:14,23:12,24:14,25:15,26:14,27:20,28:16})

        ars=wb.create_sheet("Auto Routing")
        _write_sheet(ars,["Requested Auto Tier","Sections","Model Calls","Input Tokens","Output Tokens","Reasoning Tokens","AI Credits","Actual Models"],[[tier,v.get("sections_reviewed",0),v.get("model_calls",0),v.get("input_tokens",0),v.get("output_tokens",0),v.get("reasoning_tokens",0),v.get("ai_credits",0),", ".join(v.get("actual_models",[]))] for tier,v in (consumption.get("by_auto_tier") or {}).items()])
        _format_excel_sheet(ars,{1:22,2:12,3:14,4:16,5:16,6:18,7:14,8:35})

        sws=wb.create_sheet("Scope Coverage")
        _write_sheet(sws,["Scope","Sections Reviewed","Shared Model Calls","Attribution"],[[scope,item.get("sections_reviewed",0),item.get("shared_model_calls",0),item.get("usage_attribution","")] for scope,item in by_scope.items()])
        _format_excel_sheet(sws,{1:24,2:18,3:20,4:32})

        mw=wb.create_sheet("Model Usage")
        _write_sheet(mw,["Model","Calls","Input Tokens","Output Tokens","Reasoning Tokens","AI Credits"],[[model,item.get("calls",0),item.get("input_tokens",0),item.get("output_tokens",0),item.get("reasoning_tokens",0),item.get("ai_credits_from_nano_aiu",0)] for model,item in by_model.items()])
        _format_excel_sheet(mw,{1:32,2:12,3:16,4:16,5:18,6:16})

        inv=wb.create_sheet("Section Inventory")
        # Inventory isn't included in the review result, so explain that it can be added in a future version.
        inv.append(["Note"])
        inv.append(["The current export is built from the completed review result. Section-level review evidence and AI telemetry are included; full Phase-1 inventory can be added when required."])
        _format_excel_sheet(inv,{1:110})

        notes=wb.create_sheet("Read Me")
        notes.append(["Report Notes"])
        notes.append(["Actual model/token usage is sourced from Copilot SDK telemetry when available."])
        notes.append(["Source/prompt token values marked as estimated are diagnostics only, not billing values."])
        notes.append(["When multiple review scopes share one section-level Copilot turn, usage is reported at the section/call level and is not artificially divided across scopes."])
        notes.append(["The application selects an Auto routing tier (efficiency, balance, or intelligence) based on content type, visual evidence, and selected review scopes; GitHub Copilot Auto selects the actual model."])
        notes.append(["Actual model and effective Auto tier are captured from Copilot SDK session telemetry where available. Requested tier is an application routing preference, not an assertion of the model selected."])
        notes.append(["SDK AI credits are shown as a convenience conversion from totalNanoAiu; validate current GitHub billing semantics before using for accounting."])
        notes.append(["Review failures are separated from findings and do not imply PASS."])
        notes.column_dimensions["A"].width=120
        for row in notes.iter_rows():
            for cell in row: cell.alignment=Alignment(wrap_text=True,vertical="top")

        filename=_safe_report_filename(payload.document_title)
        stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path=HLD_REPORTS_DIR/f"{Path(filename).stem}_{stamp}.xlsx"
        wb.save(out_path)
        print(f"[HLD REPORT] Excel report created: {out_path}")
        return FileResponse(out_path,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",filename=filename)
    except Exception as exc:
        print(f"[HLD REPORT ERROR] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create Excel report: {exc}")


@app.get("/api/hld/visual/{page_hash}/{section_id}/{visual_name}")
def get_hld_visual(page_hash: str, section_id: int, visual_name: str):
    """Serve a captured rendered Confluence image/diagram for UI inspection."""
    if not re.fullmatch(r"[0-9a-f]{16}", page_hash):
        raise HTTPException(status_code=400, detail="Invalid HLD page hash.")
    if not re.fullmatch(r"visual_[0-9]{2}", visual_name):
        raise HTTPException(status_code=400, detail="Invalid visual identifier.")

    path = HLD_VISUAL_CACHE_DIR / page_hash / str(section_id) / f"{visual_name}.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Visual evidence not found. Re-scrape the HLD page.")
    return FileResponse(path, media_type="image/png", filename=path.name)

    
@app.get("/api/repo/tree")
def repo_tree():
    return get_repo_tree()

@app.get("/api/file")
def file_content(path: str):

    return {
        "content":
            read_file(path)
    }

@app.post("/api/audit-flow")
def audit_flow(path: str):
    full_path = resolve_repository_file(
        path
    )

    return audit_contact_flow_file(
        full_path
    )

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

"""
@app.post("/chat")
async def chat(request):
    user_prompt = request.prompt
    tool = choose_tool(user_prompt)
    result = execute_tool(tool)
    response = summarize(result)
    return response
"""

def get_live_copilot_process():
    """Guarantees a live background communication bridge instance is running smoothly."""
    global LIVE_CO_PROCESS
    if LIVE_CO_PROCESS is not None and LIVE_CO_PROCESS.poll() is None:
        return LIVE_CO_PROCESS

    print("[SYSTEM INITIALIZATION] Spawning long-lived Copilot Generation Daemon...")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    generator_script = os.path.join(current_dir, "copilot_reviewer", "generate_diagram.mjs")
    
    custom_env = os.environ.copy()
    token_credential = os.getenv("COPILOT_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
    if token_credential:
        custom_env["GITHUB_TOKEN"] = token_credential
        custom_env["COPILOT_GITHUB_TOKEN"] = token_credential

    # Spawn process with persistent reading and writing streams attached
    LIVE_CO_PROCESS = subprocess.Popen(
        ["node", generator_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=current_dir,
        env=custom_env,
        bufsize=1 # Line buffered
    )

    def _drain_copilot_stderr(proc):
        try:
            for stderr_line in iter(proc.stderr.readline, ""):
                if stderr_line:
                    print(f"[COPILOT STDERR] {stderr_line.rstrip()}")
        except Exception as drain_error:
            print(f"[COPILOT STDERR] drain stopped: {drain_error}")

    threading.Thread(
        target=_drain_copilot_stderr,
        args=(LIVE_CO_PROCESS,),
        daemon=True,
        name="copilot-stderr-drain",
    ).start()

    return LIVE_CO_PROCESS

# ==============================================================================
# 🟢 UPDATED: ASYNC-NATIVE LOCKING FOR NON-BLOCKING EVENT LOOP
# Replace your old `threading.RLock()` with this async-safe constructor gate
# ==============================================================================
GLOBAL_ASYNC_LOCK = asyncio.Lock()


# ==============================================================================
# 🟢 UPDATED: FULLY ASYNCHRONOUS NON-BLOCKING DIAGRAM GENERATION PIPELINE
# Upgraded to `async def` to allow safe, scalable multi-user execution
# ==============================================================================
@app.post("/api/diagram/generate")
async def generate_cached_diagram(payload: DiagramGenerationRequest):

    # --- 🟢 UPGRADE: SMART SIMULATION GRID WITH JSON CONFIG LEDGER FALLBACK ---
    print(f"[SETTINGS] Simulation mode is \"{SERVER_CONFIG.enable_simulation_mode}\"")
    if SERVER_CONFIG.enable_simulation_mode:
        print(f"[⚙️ MOCK SIMULATION] Checking configuration ledger for {payload.file_path} [{payload.diagram_type}]")
        mock_graph = get_simulated_graph(payload.file_path, payload.diagram_type)
        
        if mock_graph:
            return {
                "mermaid_string": mock_graph,
                "cached": False,
                "simulated": True
            }
        else:
            # Smart default fallback if configuration matrix lacks a file-specific record entry
            print(f"[ℹ️ SIMULATION MISS] No matching record entry found. Dispatching generic chart helper.")
            fallback_chart = f"sequenceDiagram\n    autonumber\n    Client->>MockServer: Simulation Active ({payload.diagram_type})\n    Note over MockServer: File: {payload.file_path}\n    MockServer-->>Client: Standard Generic Mock Returned"
            return {
                "mermaid_string": fallback_chart,
                "cached": False,
                "simulated": True
            }

    
    # Capture original size properties before minification
    orig_chars = len(payload.file_content) if payload.file_content else 0
    orig_lines = len(payload.file_content.splitlines()) if payload.file_content else 0

    # Clean and compress code weights to save token density
    minified_content = minimize_source_code(payload.file_content)

    # Capture minified size properties
    mini_chars = len(minified_content)
    mini_lines = len(minified_content.splitlines())
    
    # Calculate difference metrics
    char_saved = orig_chars - mini_chars
    pct_saved = (char_saved / orig_chars * 100) if orig_chars > 0 else 0

    # Print structural metrics logs to the backend terminal
    print("\n" + "="*60)
    print(f"[TOKEN TRIMMER METRICS] For file: {payload.file_path}")
    print(f" -> Lines:       {orig_lines} original  -->  {mini_lines} minified (Dropped {orig_lines - mini_lines} lines)")
    print(f" -> Payload:     {orig_chars} characters -->  {mini_chars} characters")
    print(f" -> Efficiency:  Saved {char_saved} bytes/chars ({pct_saved:.1f}% reduction in prompt footprint)")
    print("="*60 + "\n")
    
    # Compute cache hash keys based on the minified string text structures
    content_bytes = minified_content.encode("utf-8")
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    cache_key = f"{payload.file_path}::{content_hash}::{payload.diagram_type}"

    # 1. Fast Cache Hit Check (Unlocked for instant reads if already calculated)
    if cache_key in BACKEND_DIAGRAM_CACHE:
        return {"mermaid_string": BACKEND_DIAGRAM_CACHE[cache_key], "cached": True}

    # --- 🟢 UPGRADE: CONDITIONAL DIAGRAM CACHING EVALUATION ---
    if SERVER_CONFIG.enable_diagram_caching and cache_key in BACKEND_DIAGRAM_CACHE:
        return {"mermaid_string": BACKEND_DIAGRAM_CACHE[cache_key], "cached": True}

    # 2. Acquire async lock before hitting the background pipe to block concurrent threads
    # Using `async with` yields execution back to the loop instead of blocking the thread
    async with GLOBAL_ASYNC_LOCK:
        # Double-check inside lock context. The second duplicate call waits at the lock gate,
        # then hits this block immediately once the first thread finishes compiling.
        if SERVER_CONFIG.enable_diagram_caching and cache_key in BACKEND_DIAGRAM_CACHE:
            print(f"[CONCURRENT ROUTE BLOCKED] Secondary port request intercepted and served from Cache.")
            return {"mermaid_string": BACKEND_DIAGRAM_CACHE[cache_key], "cached": True}

        print(f"[CACHE MISS - DIAGRAM] Fetching {payload.diagram_type} via Copilot Subprocess for {payload.file_path}")

        try:
            proc = get_live_copilot_process()
            
            script_payload = {
                "relativePath": payload.file_path,
                "source": minified_content,
                "diagramType": payload.diagram_type
            }
            
            # Send serialized instruction packet down line pipe stream
            proc.stdin.write(json.dumps(script_payload) + "\n")
            proc.stdin.flush()
            
            # 🟢 CRITICAL FIX: Run the blocking synchronous readline inside a worker thread pool executor.
            # This keeps your main FastAPI event loop completely free to handle other traffic.
            loop = asyncio.get_running_loop()
            stdout_line = await loop.run_in_executor(None, proc.stdout.readline)
            
            if not stdout_line:
                raise Exception("The background daemon dropped the connection line pipe abruptly.")
                
            parsed_response = json.loads(stdout_line.strip())
            if not parsed_response.get("success"):
                raise HTTPException(status_code=500, detail=parsed_response.get("error"))

            extracted_mermaid = parsed_response.get("mermaid_string", "").strip()
            extracted_mermaid = re.sub(r'^```[a-zA-Z0-9_-]*\s*', '', extracted_mermaid)
            extracted_mermaid = re.sub(r'\s*```$', '', extracted_mermaid).strip()

            if not extracted_mermaid:
                raise HTTPException(status_code=522, detail="Empty token payload received from pipeline.")

            # Commit value to the hot cache storage matrix
            BACKEND_DIAGRAM_CACHE[cache_key] = extracted_mermaid
            return {"mermaid_string": extracted_mermaid, "cached": False}

        except Exception as e:
            # Clean corrupt thread parameters gracefully
            # global LIVE_CO_PROCESS
            if LIVE_CO_PROCESS:
                try:
                    LIVE_CO_PROCESS.kill()
                except:
                    pass
                LIVE_CO_PROCESS = None
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))

    # Capture original size properties before minification
    orig_chars = len(payload.file_content) if payload.file_content else 0
    orig_lines = len(payload.file_content.splitlines()) if payload.file_content else 0

    # 🟢 1. NEW: Clean and compress code weights to save token density
    minified_content = minimize_source_code(payload.file_content)

    # Capture minified size properties
    mini_chars = len(minified_content)
    mini_lines = len(minified_content.splitlines())
    
    # Calculate difference metrics
    char_saved = orig_chars - mini_chars
    pct_saved = (char_saved / orig_chars * 100) if orig_chars > 0 else 0

    # 🟢 PRINT METRICS BREAKDOWN LOG TO TERMINAL
    print("\n" + "="*60)
    print(f"[TOKEN TRIMMER METRICS] For file: {payload.file_path}")
    print(f" -> Lines:       {orig_lines} original  -->  {mini_lines} minified (Dropped {orig_lines - mini_lines} lines)")
    print(f" -> Payload:     {orig_chars} characters -->  {mini_chars} characters")
    print(f" -> Efficiency:  Saved {char_saved} bytes/chars ({pct_saved:.1f}% reduction in prompt footprint)")
    print("="*60 + "\n")
    
    # 🟢 2. UPDATE: Compute cache hash keys based on the minified string text structures
    content_bytes = minified_content.encode("utf-8")
    #content_bytes = payload.file_content.encode("utf-8")
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    cache_key = f"{payload.file_path}::{content_hash}::{payload.diagram_type}"

    # 1. Fast Cache Hit Check (Unlocked for instant reads if already calculated)
    if cache_key in BACKEND_DIAGRAM_CACHE:
        return {"mermaid_string": BACKEND_DIAGRAM_CACHE[cache_key], "cached": True}

    # 2. Acquire thread lock before hitting the background pipe to block concurrent threads
    with GLOBAL_THREAD_LOCK:
        # Double-check inside lock context. The second duplicate call waits at the lock gate,
        # sthen hits this block immediately once the first thread finishes compiling.
        if cache_key in BACKEND_DIAGRAM_CACHE:
            print(f"[CONCURRENT THREAD BLOCKED] Secondary port request intercepted and served from Cache.")
            return {"mermaid_string": BACKEND_DIAGRAM_CACHE[cache_key], "cached": True}

        print(f"[CACHE MISS - DIAGRAM] Fetching {payload.diagram_type} via Copilot Subprocess for {payload.file_path}")

        try:
            proc = get_live_copilot_process()
            
            script_payload = {
                "relativePath": payload.file_path,
                "source": minified_content,
                "diagramType": payload.diagram_type
            }
            
            # Send serialized instruction packet down line pipe stream
            proc.stdin.write(json.dumps(script_payload) + "\n")
            proc.stdin.flush()
            
            # Synchronously wait for response line matching this specific thread task
            stdout_line = proc.stdout.readline()
            if not stdout_line:
                raise Exception("The background daemon dropped the connection line pipe abruptly.")
                
            parsed_response = json.loads(stdout_line.strip())
            if not parsed_response.get("success"):
                raise HTTPException(status_code=500, detail=parsed_response.get("error"))

            extracted_mermaid = parsed_response.get("mermaid_string", "").strip()
            extracted_mermaid = re.sub(r'^```[a-zA-Z0-9_-]*\s*', '', extracted_mermaid)
            extracted_mermaid = re.sub(r'\s*```$', '', extracted_mermaid).strip()

            if not extracted_mermaid:
                raise HTTPException(status_code=522, detail="Empty token payload received from pipeline.")

            # Commit value to the hot cache storage matrix
            BACKEND_DIAGRAM_CACHE[cache_key] = extracted_mermaid
            return {"mermaid_string": extracted_mermaid, "cached": False}

        except Exception as e:
            # Clean corrupt thread parameters gracefully
            # global LIVE_CO_PROCESS
            if LIVE_CO_PROCESS:
                try:
                    LIVE_CO_PROCESS.kill()
                except:
                    pass
                LIVE_CO_PROCESS = None
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/review-lambda")
def review_lambda_file(path: str):
    """
    Feeds file content into the Node.js process via standard input stream (stdin)
    matching your review_lambda.mjs protocol constraints.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    reviewer_script = os.path.join(current_dir, "copilot_reviewer", "review_lambda.mjs")
    
    # 1. Fetch source code from your local repository using your existing tool
    try:
        raw_source_code = read_file(path)
    except Exception as read_err:
        raise HTTPException(status_code=400, detail=f"Failed to load repository target: {str(read_err)}")

    # 2. Package request body to match your readStandardInput() signature
    payload = {
        "relativePath": path,
        "source": raw_source_code
    }

    # 3. Configure corporate proxy environment credentials
    print("=" * 80)
    print("ENVIRONMENT CHECK")
    print("GITHUB_TOKEN exists:", bool(os.getenv("GITHUB_TOKEN")))
    print("COPILOT_GITHUB_TOKEN exists:", bool(os.getenv("COPILOT_GITHUB_TOKEN")))
    print("=" * 80)

    custom_env = os.environ.copy()
    token_credential = (
        os.getenv("COPILOT_GITHUB_TOKEN")
        or os.getenv("GITHUB_TOKEN")
    )

    #if not token_credential:
    #    raise ValueError("Critical Error: GITHUB_TOKEN environment variable is missing!")

    if token_credential:
        custom_env["GITHUB_TOKEN"] = token_credential
        custom_env["COPILOT_GITHUB_TOKEN"] = token_credential

    try:
        print("Reviewer script:", reviewer_script)
        print("Exists:", os.path.exists(reviewer_script))
        print("Current dir:", current_dir)
        print("Node executable test...")

        print("Launching node process...")

        # 4. Open process pipe mapping stdin/stdout streams natively
        result = subprocess.run(
            ["node", reviewer_script],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd=current_dir,
            env=custom_env
        )

        print("RETURN CODE:", result.returncode)
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)

        # 6. Parse and return your structured normalized review array straight back to React
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=result.stderr
            )

        return json.loads(result.stdout.strip())

    except Exception as e:
        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# 2. Endpoint to fetch active application state flags
@app.get("/api/settings")
def get_application_settings():
    return SERVER_CONFIG

# 3. Endpoint to modify active application state flags dynamically
@app.put("/api/settings")
def update_application_settings(payload: SystemSettingsProfile):
    global SERVER_CONFIG
    SERVER_CONFIG = payload
    # 🚀 Preserves modifications permanently across restarts
    save_settings_to_file(SERVER_CONFIG)
    print(f"[⚙ SYSTEM CONFIG UPDATE] Toggles adjusted -> Caching: {SERVER_CONFIG.enable_diagram_caching}, Simulation: {SERVER_CONFIG.enable_simulation_mode}, Persistence: {SERVER_CONFIG.enable_persistence}")
    return {"success": True, "current_settings": SERVER_CONFIG}


GITHUB_WEBHOOK_SECRET = "SuperSecret123!" 

# ==========================================
# CONFIGURATION & CREDENTIALS
# ==========================================
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "SuperSecret123!")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # PAT with repo permissions

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://learningprojects.atlassian.net")
JIRA_USER_EMAIL = os.getenv("JIRA_USER_EMAIL", "dear.ramas@gmail.com")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")  # Generated from Atlassian Account Settings
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "DEV")  # e.g., 'SDLC', 'IVR', etc.


# ==========================================
# JIRA INTEGRATION SERVICE
# ==========================================
def create_jira_defect(pr_number: int, pr_url: str, defect: dict) -> str:
    """
    Creates a Bug/Defect issue in Jira for a review finding.
    Returns the created Jira issue key (e.g., 'DEV-102').
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    auth = (JIRA_USER_EMAIL, JIRA_API_TOKEN)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    description_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"Found during automated review of PR #{pr_number}.\n"}
                ]
            },
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": f"File: {defect.get('file', 'N/A')} (Line: {defect.get('line', 'N/A')})\n"},
                    {"type": "text", "text": f"Severity: {defect.get('severity', 'Medium')}\n"},
                    {"type": "text", "text": f"PR Link: {pr_url}\n\n"}
                ]
            },
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Issue Description"}]
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": defect.get("description", "")}]
            },
            {
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Recommended Remediation"}]
            },
            {
                "type": "codeBlock",
                "attrs": {"language": "python"},
                "content": [{"type": "text", "text": defect.get("suggestion", "N/A")}]
            }
        ]
    }

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": f"[PR #{pr_number} Review Defect]: {defect.get('title', 'Code Quality Issue')}",
            "description": description_adf,
            "issuetype": {"name": "Bug"},
            "labels": ["automated-review", f"pr-{pr_number}"]
        }
    }

    response = requests.post(url, json=payload, auth=auth, headers=headers, verify=False)
    if response.status_code == 201:
        issue_key = response.json()["key"]
        print(f"✅ [Jira] Successfully logged defect: {issue_key}")
        return issue_key
    else:
        print(f"❌ [Jira Error] {response.status_code}: {response.text}")
        return None


# ==========================================
# GITHUB & LLM REVIEW HELPERS
# ==========================================
def get_pr_diff(diff_url: str) -> str:
    """Fetches the unified git diff from GitHub for the PR."""
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.diff"}
    resp = requests.get(diff_url, headers=headers, verify=False)
    return resp.text if resp.status_code == 200 else ""


def analyze_diff_with_llm(diff_text: str) -> list:
    """
    Simulated LLM review agent. Analyzes diff and returns structured defects.
    (Replace with OpenAI / Copilot / Gemini API client in production).
    """
    defects = []
    
    # Example heuristic/LLM detection:
    if "password" in diff_text.lower() or "secret" in diff_text.lower():
        defects.append({
            "title": "Potential Hardcoded Secret or Plaintext Password",
            "file": "config.py",
            "line": 14,
            "severity": "High",
            "description": "Sensitive credentials or secrets appear hardcoded in the source code.",
            "suggestion": "# Use environment variables instead:\nimport os\nSECRET = os.getenv('APP_SECRET')"
        })
    if "select *" in diff_text.lower():
        defects.append({
            "title": "Unbounded Query Performance Defect",
            "file": "database.py",
            "line": 42,
            "severity": "Medium",
            "description": "Using SELECT * can cause latency and excessive memory usage on large tables.",
            "suggestion": "SELECT id, status, created_at FROM tbl..."
        })
        
    return defects


def post_github_pr_comment(comments_url: str, created_jira_keys: list):
    """Posts a comment on the GitHub PR listing the raised Jira defects."""
    if not created_jira_keys:
        body = "✅ **Automated Review:** No critical defects found. Code looks clean!"
    else:
        links = "\n".join([f"- [{key}]({JIRA_BASE_URL}/browse/{key})" for key in created_jira_keys])
        body = f"⚠️ **Automated Review:** The following review defects were raised in Jira:\n\n{links}\n\nPlease resolve them before merge."

    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    requests.post(comments_url, json={"body": body}, headers=headers, verify=False)


# ==========================================
# WEBHOOK ENDPOINT
# ==========================================
@app.post("/webhook/github", status_code=status.HTTP_200_OK)
async def handle_github_webhook(
    request: Request,
    x_github_event: str = Header(...)
):
    raw_body = await request.body()
    payload = json.loads(raw_body)

    if x_github_event == "pull_request":
        action = payload.get("action")
        pr_data = payload.get("pull_request", {})
        pr_number = pr_data.get("number")
        pr_url = pr_data.get("html_url")
        diff_url = pr_data.get("diff_url")
        comments_url = pr_data.get("comments_url")

        # Trigger analysis when PR is opened or new commits are pushed (synchronize)
        if action in ["opened", "synchronize"]:
            print(f"\n🔍 [Reviewer] Starting automated review for PR #{pr_number}...")
            
            # 1. Fetch Diff
            diff = get_pr_diff(diff_url)
            
            # 2. Run LLM Analysis
            defects = analyze_diff_with_llm(diff)
            print(f"📊 [Reviewer] Found {len(defects)} defects.")

            # 3. Create Jira Defect Issues
            created_keys = []
            for defect in defects:
                issue_key = create_jira_defect(pr_number, pr_url, defect)
                if issue_key:
                    created_keys.append(issue_key)

            # 4. Comment on PR
            post_github_pr_comment(comments_url, created_keys)

    return {"status": "success", "event": x_github_event}

