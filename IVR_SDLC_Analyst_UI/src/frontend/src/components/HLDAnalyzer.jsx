import { useState } from "react";

export default function HLDAnalyzer() {
    const [title, setTitle] = useState("Unfinished IVR HLD Documentation");
    const [pastedText, setPastedText] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [analysisResult, setAnalysisResult] = useState(null);

    // Path 1: Process text values directly from the editor textarea
    async function handleTextSubmission() {
        if (!pastedText.trim()) {
            setError("Please paste raw text or markdown before submitting.");
            return;
        }
        submitToBackend(title, pastedText);
    }

    // Path 2: Intercept local system text/.html exports using standard file reader streams
    function handleFileSelection(e) {
        const file = e.target.files[0];
        if (!file) return;

        setError("");
        setTitle(file.name.replace(/\.[^/.]+$/, "")); // Strip file format tokens

        const reader = new FileReader();
        reader.onload = (event) => {
            let fileContent = event.target.result;
            
            // Clean up basic HTML tags if an exported wiki page is dropped
            if (file.name.endsWith(".html") || file.name.endsWith(".htm")) {
                const tempDiv = document.createElement("div");
                tempDiv.innerHTML = fileContent;
                fileContent = tempDiv.innerText || tempDiv.textContent || "";
            }
            setPastedText(fileContent);
        };
        reader.onerror = () => setError("Failed reading local system document asset.");
        reader.readAsText(file);
    }

    async function submitToBackend(docTitle, docContent) {
        setLoading(true);
        setError("");
        setAnalysisResult(null);

        try {
            const response = await fetch("http://127.0.0", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    document_title: docTitle,
                    raw_content: docContent,
                    project_scope: "IVR Analysis Engine Workflow"
                })
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || "FastAPI processing pipeline crashed.");
            }

            const data = await response.json();
            setAnalysisResult(data.segmented_blueprint);
        } catch (err) {
            setError(err.message || "Failed communicating with backend services.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <section className="hld-analyzer-panel" style={{ padding: "20px", fontFamily: "Segoe UI, sans-serif" }}>
            <div style={{ marginBottom: "20px" }}>
                <h2 style={{ margin: 0, color: "#18181b" }}>HLD Analyzer Console</h2>
                <p style={{ color: "#71717a", margin: "4px 0" }}>Extract and segment wiki design specifications via GitHub Copilot Reviewer.</p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                {/* Left Side Ingestion Interface Form Column */}
                <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                    <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "6px" }}>Document Reference Title</label>
                        <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} style={{ width: "100%", padding: "8px", border: "1px solid #d4d4d8", borderRadius: "4px" }} />
                    </div>

                    <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "6px" }}>Ingestion Pathway 1: Upload Exported Document (.txt, .html)</label>
                        <input type="file" accept=".txt,.html,.htm" onChange={handleFileSelection} style={{ display: "block" }} />
                    </div>

                    <div>
                        <label style={{ fontWeight: "600", display: "block", marginBottom: "6px" }}>Ingestion Pathway 2: Paste Raw Wiki Document Context</label>
                        <textarea rows={16} value={pastedText} onChange={(e) => setPastedText(e.target.value)} placeholder="Paste text content scraped via your Edge Bookmarklet script here..." style={{ width: "100%", padding: "8px", border: "1px solid #d4d4d8", borderRadius: "4px", fontFamily: "monospace" }} />
                    </div>

                    <button onClick={handleTextSubmission} disabled={loading} style={{ background: "#0f6cbd", color: "#fff", padding: "10px", border: "none", borderRadius: "4px", fontWeight: "600", cursor: loading ? "not-allowed" : "pointer" }}>
                        {loading ? "Analyzing Document Architecture..." : "Trigger AI Segmentation Pipeline"}
                    </button>

                    {error && <div style={{ color: "#ef4444", background: "#fef2f2", padding: "10px", borderRadius: "4px", border: "1px solid #fca5a5" }}>{error}</div>}
                </div>

                {/* Right Side AI Real-time Analytical Output Grid Column */}
                <div style={{ background: "#f8fafc", padding: "16px", borderRadius: "6px", border: "1px solid #e2e8f0", overflowY: "auto", maxHeight: "600px" }}>
                    <h3 style={{ margin: "0 0 12px 0", color: "#334155" }}>Structured Output Blueprints</h3>
                    
                    {!analysisResult && !loading && <div style={{ color: "#94a3b8", fontStyle: "italic" }}>Awaiting document streaming extraction tasks...</div>}
                    {loading && <div><span className="loading-spinner" /> Running multi-pass context grouping partitioning transforms...</div>}

                    {analysisResult && (
                        <div>
                            <div style={{ background: "#e0f2fe", padding: "8px", borderRadius: "4px", marginBottom: "14px", fontSize: "0.85rem", color: "#0369a1" }}>
                                <strong>Success:</strong> Found {analysisResult.document_metadata?.segments_found || 0} modular parameters.
                            </div>

                            <h4 style={{ color: "#0f6cbd", margin: "10px 0 6px 0" }}>🔍 Code Review Target Sections</h4>
                            {analysisResult.review_required_sections?.map((sec, idx) => (
                                <div key={idx} style={{ background: "#fff", border: "1px solid #cbd5e1", padding: "10px", borderRadius: "4px", marginBottom: "8px" }}>
                                    <strong>{sec.section_title}</strong>
                                    <p style={{ margin: "4px 0", fontSize: "0.85rem", color: "#64748b" }}>{sec.context_summary}</p>
                                    <pre style={{ margin: "4px 0", background: "#f1f5f9", padding: "6px", fontSize: "0.8rem", whiteSpace: "pre-wrap" }}>{sec.raw_text_content}</pre>
                                </div>
                            ))}

                            <h4 style={{ color: "#16a34a", margin: "16px 0 6px 0" }}>📞 IVR Connect Functional Requirements</h4>
                            {analysisResult.ivr_flow_requirements?.map((flow, idx) => (
                                <div key={idx} style={{ background: "#fff", border: "1px solid #cbd5e1", padding: "10px", borderRadius: "4px", marginBottom: "8px" }}>
                                    <strong>{flow.flow_name}</strong>
                                    <div style={{ fontSize: "0.85rem", margin: "2px 0" }}><em>Trigger:</em> {flow.trigger_condition}</div>
                                    <ul style={{ margin: "6px 0 0 0", paddingLeft: "20px", fontSize: "0.85rem" }}>
                                        {flow.intended_steps?.map((step, sIdx) => <li key={sIdx}>{step}</li>)}
                                    </ul>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
}
