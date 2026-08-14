const API_URL = "http://localhost:8000/api";

export async function loadRepoTree() {

    const response =
        await fetch(`${API_URL}/repo/tree`);

    return await response.json();
}

export async function loadFile(path) {

    console.log(
        "Loading file:",
        path
    );

    const response =
        await fetch(
            `${API_URL}/file?path=${encodeURIComponent(path)}`
        );

    console.log(response);

    return await response.json();
}