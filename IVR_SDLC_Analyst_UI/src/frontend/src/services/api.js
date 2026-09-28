const API_URL = "http://localhost:8000/api";

async function parseResponse(response) {
    const data = await response.json();

    if (!response.ok) {
        const message =
            data?.detail ||
            data?.message ||
            `Request failed with status ${response.status}`;

        throw new Error(message);
    }

    return data;
}

export async function loadRepoTree() {
    const response = await fetch(
        `${API_URL}/repo/tree`
    );

    return parseResponse(response);
}

export async function loadFile(path) {
    const response = await fetch(
        `${API_URL}/file?path=${encodeURIComponent(path)}`
    );

    return parseResponse(response);
}

export async function auditFlow(path) {
    const response = await fetch(
        `${API_URL}/audit-flow?path=${encodeURIComponent(path)}`,
        {
            method: "POST",
            headers: {
                Accept: "application/json",
            },
        }
    );

    return parseResponse(response);
}

// Append this function to src/frontend/src/services/api.js

export async function requestLambdaReview(path) {
    console.error("Requesting Copilot review for asset:", path);

    const response = await fetch(
        `${API_URL}/review-lambda?path=${encodeURIComponent(path)}`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        }
    );

    if (!response.ok) {
        throw new Error("Failed to compile Copilot review report.");
    }

    return await response.json();
}

// 🟢 Update this function inside your src/frontend/src/services/api.js file

export async function requestDiagramGeneration(path, content, diagramType) {
    console.warn(`Fetching ${diagramType} diagram from FastAPI for:`, path);

    const response = await fetch(`${API_URL}/diagram/generate`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            file_path: path,
            file_content: content,
            diagram_type: diagramType
        })
    });

    if (!response.ok) {
        throw new Error(`Failed to compile ${diagramType} diagram chart via backend services.`);
    }

    const data = await response.json();
    
    // 🟢 CRITICAL EXTRACTION FIX: Ensure we return the absolute raw string text value
    // If the data object itself is somehow a string, parse it first to break down double-encodings
    if (typeof data === "string") {
        const parsed = JSON.parse(data);
        return parsed.mermaid_string || parsed;
    }
    
    return data.mermaid_string || data; 
}


// Append these functions to the bottom of src/frontend/src/services/api.js

/**
 * Phase 1: Ingests an HLD file to generate or load the verification matrix chunk array.
 */
/**
 * Phase 1 Updated: Ingests a Confluence Wiki URL string parameters object 
 * to generate or load the verification matrix chunk array.
 */
export async function generateHLDMatrix(pageUrl, { forceRefresh = false } = {}) {
    const response = await fetch(`${API_URL}/hld/generate-matrix`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            page_url: pageUrl,
            force_refresh: Boolean(forceRefresh),
        })
    });

    return parseResponse(response);
}

/**
 * Metadata-first document revision check is implemented by the
 * /hld/generate-matrix endpoint. With forceRefresh=false the backend may
 * return a confirmation gate instead of extracting the complete matrix.
 */
export async function checkHLDDocument(pageUrl) {
    return generateHLDMatrix(pageUrl, { forceRefresh: false });
}


/**
 * Clear the saved server cache for a specific document filename.
 */
export async function clearHLDMatrixCache(filename) {
    const response = await fetch(`${API_URL}/hld/clear-matrix-cache`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ filename })
    });

    return parseResponse(response);
}

/**
 * Phase 2: Triggers the backend Copilot Daemon processing session for the validated matrix.
 */
export async function runCopilotHLDAudit(filename) {
    const response = await fetch(`${API_URL}/hld/ingest`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            document_title: filename,
            raw_content: "ALREADY_CACHED_ON_DISK",
            project_scope: "IVR Analysis Engine Framework Workflow"
        })
    });

    return parseResponse(response);
}

export async function listReviewJobs({ status = "", search = "", documentUrl = "", limit = 100, offset = 0 } = {}) {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (search) params.set("search", search);
    if (documentUrl) params.set("document_url", documentUrl);
    params.set("limit", String(limit));
    params.set("offset", String(offset));

    const response = await fetch(`${API_URL}/hld/jobs?${params.toString()}`);
    return parseResponse(response);
}

export async function getReviewJob(jobId) {
    const response = await fetch(`${API_URL}/hld/jobs/${encodeURIComponent(jobId)}`);
    return parseResponse(response);
}

export async function deleteReviewJob(jobId) {
    const response = await fetch(`${API_URL}/hld/jobs/${encodeURIComponent(jobId)}`, {
        method: "DELETE",
    });
    return parseResponse(response);
}

export async function clearCompletedReviewJobs(jobIds = null) {
    const response = await fetch(`${API_URL}/hld/jobs/completed`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(jobIds ? { job_ids: jobIds } : {}),
    });
    return parseResponse(response);
}
