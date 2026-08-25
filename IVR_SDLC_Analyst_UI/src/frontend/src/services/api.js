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


