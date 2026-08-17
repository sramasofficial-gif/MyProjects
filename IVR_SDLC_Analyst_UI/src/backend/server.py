# MyProjects/IVR_SDLC_Analyst_UI/src/backend/server.py
import os
import subprocess
import json
from fastapi import HTTPException
from services.repo_tools import read_file  # Import your existing file reader
from fastapi import FastAPI

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
    custom_env = os.environ.copy()
    token_credential = os.getenv("GITHUB_TOKEN")

    if not token_credential:
        raise ValueError("Critical Error: GITHUB_TOKEN environment variable is missing!")

    custom_env["GITHUB_TOKEN"] = token_credential
    custom_env["COPILOT_GITHUB_TOKEN"] = token_credential

    try:
        # 4. Open process pipe mapping stdin/stdout streams natively
        process = subprocess.Popen(
            ["node", reviewer_script],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=current_dir,
            env=custom_env
        )

        # 5. Push the JSON string payload directly into your script's for-await loop
        stdout_data, stderr_data = process.communicate(input=json.dumps(payload))

        if process.returncode != 0:
            raise HTTPException(
                status_code=500, 
                detail=f"Copilot Node process exited with error: {stderr_data or stdout_data}"
            )

        # 6. Parse and return your structured normalized review array straight back to React
        return json.loads(stdout_data.strip())

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
