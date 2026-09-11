const extractError = async (response) => {
  try {
    const body = await response.json();
    return body.detail || "The server could not process the document.";
  } catch {
    return "The server could not process the document.";
  }
};

export async function extractSections(file, signal) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/v1/documents/extract-sections", {
    method: "POST",
    body: formData,
    signal,
  });

  if (!response.ok) {
    throw new Error(await extractError(response));
  }
  return response.json();
}
