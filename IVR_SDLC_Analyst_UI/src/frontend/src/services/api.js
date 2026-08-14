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