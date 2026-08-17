
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

python -m venv .venv

.venv\Scripts\activate

python -m pip install fastapi uvicorn python-multipart

python -m pip list

## Start FastAPI

cd src\backend
python -m uvicorn server:app --reload

Expected Output :

(.venv) C:\Users\ramasubramanians\OneDrive - HCL TECHNOLOGIES LIMITED\Documents\HS\Training\MyProjects\IVR_SDLC_Analyst_UI\src\backend>python -m uvicorn server:app --reload
INFO:     Will watch for changes in these directories: ['C:\\Users\\ramasubramanians\\OneDrive - HCL TECHNOLOGIES LIMITED\\Documents\\HS\\Training\\MyProjects\\IVR_SDLC_Analyst_UI\\src\\backend']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [55196] using StatReload
INFO:     Started server process [33584]
INFO:     Waiting for application startup.
INFO:     Application startup complete.

## From Windows Browser 

http://localhost:8000/docs

## Testing

### API - GET /api/repo/tree

curl -X 'GET' \
  'http://localhost:8000/api/repo/tree' \
  -H 'accept: application/json'

Response: 

[
  {
    "folder": ".",
    "files": [
      "contact_flow_audit_summary.csv",
      "contact_flow_audit_summary.md"
    ]
  },
  {
    "folder": "contact-flows",
    "files": [
      "cfAccountStatus.json",
      "cfAccountSummaryInfo.json",
      "cfActivateCard.json",
      "cfAgentOnHold.json",
      "cfAgentUI.json"
    ]
  },
  {
    "folder": "terraform",
    "files": [
      "admin_objects.tf",
      "amazon-connect-data-tables.tf",
      "awscc_rp.tf",
      "backend.tf",
      "connect_locals.tf",
      "contactflow-variables.tf",
      "contact_flows.tf",
      "core_connect.tf",
      "data.tf",
      "dev.auto.tfvars",
      "dev.contactflow.auto.tfvars",
      "event_bridge.tf",
      "main.tf",
      "provider.tf",
      "Readme.md",
      "s3.tf",
      "ses.tf",
      "sns.tf",
      "storage.tf",
      "task-template.tf",
      "vars.tf"
    ]
  }
]


### API - GET GET /api/file?path=contact-flows%2FcfAccountStatus.json

curl -X 'GET' \
  'http://localhost:8000/api/file?path=contact-flows%2FcfAccountStatus.json' \
  -H 'accept: application/json'

  Response :

  <file content>


  ### API - POST /api/audit-flow?path=contact-flows%2FcfAccountStatus.json

  curl -X 'POST' \
  'http://localhost:8000/api/audit-flow?path=contact-flows%2FcfAccountStatus.json' \
  -H 'accept: application/json' \
  -d ''

  Response :

  {
  "success": true,
  "audit_passed": false,
  "metrics": {
    "flow_name": "cfAccountStatus.json",
    "file_name": "cfAccountStatus.json",
    "total_blocks": 64,
    "total_edges": 154,
    "cyclomatic_complexity_mccabe": 92,
    "cyclomatic_complexity_decision": 94,
    "lambda_integrations": 7,
    "lambda_action_ids": [
      "prompt defaults-copy-1",
      "prompt defaults",
      "GetAccountStatus",
      "efcbc582-2231-4226-8c9c-5a786e8748e5",
      "96158c60-51d0-4428-872c-260aad0c9759",
      "c63611a3-662f-4d8d-9478-2de17876d415",
      "253a0204-fb09-426f-b72f-589aac24d6e0"
    ],
    "unhandled_error_blocks": 0,
    "unhandled_error_action_ids": [],
    "invalid_action_entries": 0
  },
  "status": {
    "complexity": {
      "level": "fail",
      "label": "High Risk",
      "message": "The contact flow should be considered for refactoring or decomposition."
    },
    "flow_size": {
      "level": "fail",
      "label": "Oversized Flow",
      "message": "Consider splitting the flow into smaller reusable contact flows or flow modules."
    }
  },
  "recommendations": [
    "Reduce decision branches or divide the flow into smaller reusable modules.",
    "Review whether groups of actions can be moved into separate flows or Amazon Connect flow modules.",
    "Verify timeout, failure, malformed response, and retry handling for the Lambda integrations."
  ]
}
===========================================================

Install react
--------------

Get-ChildItem

Get-ChildItem -Recurse -Filter package.json

npm install

cd MyProjects\IVR_SDLC_Analyst_UI\src

npm create vite@latest frontend -- --template react

-----------------
Output
------

(.venv) PS C:\Users\ramasubramanians\OneDrive - HCL TECHNOLOGIES LIMITED\Documents\HS\Training\MyProjects\IVR_SDLC_Analyst_UI\src> npm create vite@latest frontend -- --template react
Need to install the following packages:
create-vite@9.1.2
Ok to proceed? (y) y

> npx
> create-vite frontend --template react

│
◇  Which linter to use?
│  Oxlint
│
◇  Install with npm and start now?
│  Yes
│
◇  Scaffolding project in C:\Users\ramasubramanians\OneDrive - HCL TECHNOLOGIES LIMITED\Documents\HS\Training\MyProjects\IVR_SDLC_Analyst_UI\src\frontend...
│
◇  Installing dependencies with npm...

added 24 packages, and audited 25 packages in 21s

9 packages are looking for funding
  run `npm fund` for details

found 0 vulnerabilities
│
◇  Starting dev server...

> frontend@0.0.0 dev
> vite


  VITE v8.2.1  ready in 418 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help


Or when react is already available, use following to start front end server:

cd src\frontend
npm run dev

In a browser :

http://localhost:5173     (Front end)

http://127.0.0.1:8000/docs  (FastAPI backend)


powershell -ExecutionPolicy Bypass -Command "npm list @github/copilot-sdk"

winget install --id github.cli

gh extension install github/gh-copilot

copilot auth login


1) Open your browser and navigate to github.com -> Settings -> Developer Settings -> Personal Access Tokens -> Tokens (classic).
2) Click Generate new token (classic).
3) Provide a clear descriptive note (e.g., IVR_SDLC_Analyst_Token).
4) Select the necessary scopes dictated by your enterprise profile: typically repo (for file context read-access) and read:org (if your enterprise seats require org-level checks).
5) Generate the token and immediately copy the string starting with ghp_....


Get-Content test_payload.json | node review_lambda.mjs


pip install python-dotenv

$env:GITHUB_TOKEN="YOUR_PAT_TOKEN"

export GITHUB_TOKEN="YOUR_PAT_TOKEN"