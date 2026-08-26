# MyProjects/IVR_SDLC_Analyst_UI/src/backend/server.py
import os
import subprocess
import json
import traceback
from fastapi import HTTPException
from services.repo_tools import read_file  # Import your existing file reader
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import asyncio # 🟢 Ensure this is imported at the top of server.py
import threading  # 🟢 NEW: Import native thread locking module
import hashlib
from pydantic import BaseModel
import re

# Cache storage tracking memory arrays
BACKEND_DIAGRAM_CACHE = {}

# 🟢 Global execution pointer referencing our live background Node service thread daemon
LIVE_CO_PROCESS = None

# 🟢 CRITICAL DUAL-CALL LOCK PROTECTION: Global re-entrant lock structure
GLOBAL_THREAD_LOCK = threading.RLock()

class DiagramGenerationRequest(BaseModel):
    file_path: str
    file_content: str
    diagram_type: str

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

from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
    
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

from services.repo_tools import (
    get_repo_tree
)

import re # Ensure re is imported at the top of your server.py file

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

@app.post("/api/diagram/generate")
def generate_cached_diagram(payload: DiagramGenerationRequest):
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
            global LIVE_CO_PROCESS
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

