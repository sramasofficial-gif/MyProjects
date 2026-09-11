import { useEffect, useRef, useState } from "react";
import FileDropZone from "./components/FileDropZone";
import SectionSelector from "./components/SectionSelector";
import { extractSections } from "./services/api";

export default function App() {
  const [result, setResult] = useState(null);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const abortRef = useRef(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  const handleFile = async (file) => {
    const extension = file.name.toLowerCase().split(".").pop();
    if (!["mhtml", "mht"].includes(extension)) {
      setError("Select a file with the .mhtml or .mht extension.");
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError("");

    try {
      const response = await extractSections(file, controller.signal);
      setResult(response);
      setSelectedIds(new Set());
    } catch (requestError) {
      if (requestError.name !== "AbortError") {
        setError(requestError.message || "Unable to extract sections.");
      }
    } finally {
      if (abortRef.current === controller) setLoading(false);
    }
  };

  const reset = () => {
    abortRef.current?.abort();
    setResult(null);
    setSelectedIds(new Set());
    setError("");
    setLoading(false);
  };

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand-mark">HLD</div>
        <div>
          <h1>HLD Review Assistant</h1>
          <p>Extract and select reviewable sections from an MHTML design document.</p>
        </div>
      </header>

      {error && <div className="error-banner" role="alert">{error}</div>}
      {loading && (
        <div className="loading-card" role="status">
          <span className="spinner" />
          Reading the MHTML and detecting HLD sections...
        </div>
      )}
      {!loading && !result && <FileDropZone disabled={loading} onFileSelected={handleFile} />}
      {!loading && result && (
        <SectionSelector
          result={result}
          selectedIds={selectedIds}
          onSelectionChange={setSelectedIds}
          onReset={reset}
        />
      )}
    </main>
  );
}
