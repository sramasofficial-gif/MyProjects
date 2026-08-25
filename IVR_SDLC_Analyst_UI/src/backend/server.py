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
import hashlib
from pydantic import BaseModel

# Cache storage tracking memory arrays
BACKEND_DIAGRAM_CACHE = {}

# 🟢 Thread-safe locks lookup map to shield background sub-processes
DIAGRAM_LOCKS = {}

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

import re # Make sure to import re at the top of your file if it isn't there


@app.post("/api/diagram/generate")
async def generate_cached_diagram(payload: DiagramGenerationRequest):
    content_bytes = payload.file_content.encode("utf-8")
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    cache_key = f"{payload.file_path}::{content_hash}::{payload.diagram_type}"

    # 1. Immediate Cache Hit validation
    if cache_key in BACKEND_DIAGRAM_CACHE:
        print(f"[CACHE HIT - DIAGRAM] Serving {payload.diagram_type} for {payload.file_path}")
        return {"mermaid_string": BACKEND_DIAGRAM_CACHE[cache_key], "cached": True}

    # 2. Allocate or acquire an execution lock specific to this hash key signature
    if cache_key not in DIAGRAM_LOCKS:
        DIAGRAM_LOCKS[cache_key] = asyncio.Lock()
        
    async with DIAGRAM_LOCKS[cache_key]:
        # Double-check inside the lock context (the second request waits here, then hits the cache immediately)
        if cache_key in BACKEND_DIAGRAM_CACHE:
            print(f"[CONCURRENT BLOCKED] Secondary thread serving from newly compiled cache asset.")
            return {"mermaid_string": BACKEND_DIAGRAM_CACHE[cache_key], "cached": True}

        print(f"[CACHE MISS - DIAGRAM] Fetching {payload.diagram_type} via Copilot Subprocess for {payload.file_path}")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        generator_script = os.path.join(current_dir, "copilot_reviewer", "generate_diagram.mjs")
        
        if not os.path.exists(generator_script):
            raise HTTPException(status_code=500, detail="The background script generate_diagram.mjs is missing.")

        script_payload = {
            "relativePath": payload.file_path,
            "source": payload.file_content,
            "diagramType": payload.diagram_type
        }

        custom_env = os.environ.copy()
        token_credential = os.getenv("COPILOT_GITHUB_TOKEN") or os.getenv("GITHUB_TOKEN")
        if token_credential:
            custom_env["GITHUB_TOKEN"] = token_credential
            custom_env["COPILOT_GITHUB_TOKEN"] = token_credential

        try:
            # Run the subprocess thread safely
            result = await asyncio.to_thread(
                subprocess.run,
                ["node", generator_script],
                input=json.dumps(script_payload),
                capture_output=True,
                text=True,
                cwd=current_dir,
                env=custom_env
            )

            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Engine runtime error: {result.stderr}")

            parsed_response = json.loads(result.stdout.strip())
            
            if not parsed_response.get("success"):
                raise HTTPException(status_code=500, detail=parsed_response.get("error", "Unknown pipeline error."))

            print(f"[PARSED RESPONSE] {parsed_response}")
            extracted_mermaid = parsed_response.get("mermaid_string", "").strip()

            # Clean up all markdown code fence leaks completely
            extracted_mermaid = re.sub(r'^```[a-zA-Z0-9_-]*\s*', '', extracted_mermaid)
            extracted_mermaid = re.sub(r'\s*```$', '', extracted_mermaid).strip()

            print(f"[EXTRACTED RESPONSE] {extracted_mermaid}")

            # 🟢 CRITICAL SECURITY FIX: Never cache or return an empty string
            if not extracted_mermaid:
                print(f"[ERROR] Copilot returned an empty string for {payload.file_path}")
                raise HTTPException(
                    status_code=522, 
                    detail="GitHub Copilot generated an empty string payload. Please try again."
                )

            # Save clean syntax straight into your caching systems
            BACKEND_DIAGRAM_CACHE[cache_key] = extracted_mermaid
            return {"mermaid_string": extracted_mermaid, "cached": False}

        except Exception as e:
            print(traceback.format_exc())
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))
        
        finally:
            # Clean up active memory allocation tracking locks cleanly
            if cache_key in DIAGRAM_LOCKS and not DIAGRAM_LOCKS[cache_key].locked():
                del DIAGRAM_LOCKS[cache_key]

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

