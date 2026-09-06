# MyProjects/IVR_SDLC_Analyst_UI/src/backend/server.py
import shutil
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
import hashlib
from pathlib import Path

from pydantic import BaseModel
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form

from services.repo_tools import read_file  # Import your existing file reader

from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import concurrent.futures
from functools import partial

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
    
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Cache storage tracking memory arrays
BACKEND_DIAGRAM_CACHE = {}

# Global pointer for temporary state storage between Phase-1 and Phase-2
LATEST_MATRIX_CACHE_PATH = "prioritized_audit_chunks.json"

# 🟢 Global execution pointer referencing our live background Node service thread daemon
LIVE_CO_PROCESS = None

# 🟢 CRITICAL DUAL-CALL LOCK PROTECTION: Global re-entrant lock structure
GLOBAL_THREAD_LOCK = threading.RLock()

# Binds paths to local config sheets safely
CONFIG_DIR = Path(__file__).resolve().parent / "conf"
SETTINGS_FILE_PATH = os.path.join(CONFIG_DIR, "server_settings.json")
SIMULATION_FILE_PATH = os.path.join(CONFIG_DIR, "simulation_graphs.json")

# 1. Map Schema models for the Wiki extraction payload boundaries
class HLDIngestionRequest(BaseModel):
    document_title: str
    raw_content: str
    project_scope: Optional[str] = "IVR Context Validation"

class DiagramGenerationRequest(BaseModel):
    file_path: str
    file_content: str
    diagram_type: str

# 1. Define Server Controls Configuration Model State Schema
class SystemSettingsProfile(BaseModel):
    enable_diagram_caching: bool = True
    enable_simulation_mode: bool = True
    enable_persistence: bool = True


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

# --- Phase 1: Ingestion & Matrix Compiling Endpoint ---
def get_file_cache_path(filename: str) -> str:
    """Generates an isolated storage filename based on the document name."""
    # Sanitize filename to prevent directory traversal issues
    safe_name = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in ['.', '_', '-']]).strip()
    return f"matrix_cache_{safe_name}.json"


@app.post("/api/hld/generate-matrix")
async def generate_verified_matrix(file: UploadFile = File(...)):
    """
    Phase 1: Ingests an HLD, checks if a cache file exists for this specific filename,
    and returns it instantly. Otherwise, runs the full OCR/Parsing pipeline.
    """
    _, file_ext = os.path.splitext(file.filename)
    file_ext = file_ext.lower()

    target_cache_path = get_file_cache_path(file.filename)

    # 🟢 CHECK FILENAME CACHE FIRST: Instant load if this specific file was processed earlier
    if SERVER_CONFIG.enable_persistence and os.path.exists(target_cache_path):
        print(f"[CACHE HIT] Serving pre-existing matrix for file: {file.filename}")
        with open(target_cache_path, "r", encoding="utf-8") as f:
            matrix_chunks = json.load(f)
        return {
            "success": True,
            "filename": file.filename,
            "matrix": matrix_chunks,
            "loaded_from_cache": True
        }

    # Cache Miss: Run your standard local extraction steps
    temp_file_path = f"temp_upload_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        raw_text_extracted = ""
        if file_ext == ".pdf":
            extractor = DynamicPDFExtractor(temp_file_path)
            raw_text_extracted = extractor.extract_clean_text()
        elif file_ext in [".txt", ".html", ".htm"]:
            with open(temp_file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text_extracted = f.read()

        # Build chunks structure array matrix
        chunker = HLDAuditChunker(target_chunk_size=1000, overlap=150)
        matrix_chunks = chunker.create_audit_chunks(raw_text_extracted)

        # 🟢 UPGRADE: CONDITIONAL DISK SERIALIZATION
        # Only dump the tracking matrix array out to a hard cache file if persistence is true
        if SERVER_CONFIG.enable_persistence:
            # Save to disk using the specific filename key
            with open(target_cache_path, "w", encoding="utf-8") as f:
                json.dump(matrix_chunks, f, indent=2)
            print(f"[PERSISTENCE] Matrix successfully serialized to disk for: {file.filename}")
        else:
            print(f"[DEVELOPMENT MODE] Skipping local disk serialization files cache dump.")


        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        return {
            "success": True,
            "filename": file.filename,
            "matrix": matrix_chunks,
            "loaded_from_cache": False
        }

    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hld/clear-matrix-cache")
def clear_matrix_cache(payload: dict):
    """
    Deletes the saved JSON file for a specific filename, forcing a fresh re-parse.
    """
    filename = payload.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="Missing target filename identifier.")
        
    target_cache_path = get_file_cache_path(filename)
    if os.path.exists(target_cache_path):
        os.remove(target_cache_path)
        print(f"[CACHE RESET] Cleared cached matrix for: {filename}")
        return {"success": True, "message": "Cache successfully cleared."}
    return {"success": True, "message": "No cache found for this file."}

@app.post("/api/hld/ingest")
def ingest_and_segment_hld(payload: HLDIngestionRequest):
    """
    Phase 2: Reads the validated local matrix from disk, filters targets,
    and runs them sequentially through the long-lived Copilot Daemon.
    """
    target_cache_path = get_file_cache_path(payload.document_title)

    if not os.path.exists(target_cache_path):
        raise HTTPException(status_code=404, detail="No verification matrix found. Please run Phase-1 first.")

    print(f"[HLD AUDIT] Loading cached matrix for: {payload.document_title}")
    
    # 1. Load the locally saved matrix chunks
    with open(target_cache_path, "r", encoding="utf-8") as f:
        matrix_chunks = json.load(f)
        
    aggregated_blueprint = {
        "document_metadata": { "title": payload.document_title, "segments_found": 0 },
        "review_required_sections": [],
        "ivr_flow_requirements": []
    }

    try:
        proc = get_live_copilot_process()
        
        # 2. Filter and loop through chunks with identified risks
        for idx, chunk in enumerate(matrix_chunks):
            tags = chunk["metadata"]["audit_tags"]
            header_context = chunk["metadata"]["parent_section"]
            
            # Skip filler pages to optimize tokens
            if not tags:
                continue
                
            print(f"   ↳ Auditing block {idx+1}/{len(matrix_chunks)}: [{header_context}]")
            
            script_payload = {
                "relativePath": f"{payload.document_title} -> {header_context}",
                "source": chunk["content"],
                "diagramType": "HLD_SEGMENTATION_MODE"
            }

            proc.stdin.write(json.dumps(script_payload) + "\n")
            proc.stdin.flush()
            
            stdout_line = proc.stdout.readline()
            if not stdout_line:
                raise Exception("Copilot background daemon disconnected.")
                
            response_data = json.loads(stdout_line.strip())
            if not response_data.get("success"):
                continue

            raw_json_str = response_data.get("mermaid_string", "").strip()
            raw_json_str = re.sub(r'^```(?:json)?\s*', '', raw_json_str, flags=re.IGNORECASE)
            raw_json_str = re.sub(r'\s*```$', '', raw_json_str).strip()

            try:
                chunk_blueprint = json.loads(raw_json_str)
                if "review_required_sections" in chunk_blueprint:
                    aggregated_blueprint["review_required_sections"].extend(chunk_blueprint["review_required_sections"])
                if "ivr_flow_requirements" in chunk_blueprint:
                    aggregated_blueprint["ivr_flow_requirements"].extend(chunk_blueprint["ivr_flow_requirements"])
            except json.JSONDecodeError:
                continue

        total_segments = len(aggregated_blueprint["review_required_sections"]) + len(aggregated_blueprint["ivr_flow_requirements"])
        aggregated_blueprint["document_metadata"]["segments_found"] = total_segments

        return {
            "success": True,
            "document_title": payload.document_title,
            "segmented_blueprint": aggregated_blueprint
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
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