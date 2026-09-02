import { useState } from "react";
import { generateHLDMatrix, clearHLDMatrixCache, runCopilotHLDAudit } from "../services/api";

export default function HLDAnalyzer() {
    const [selectedFile, setSelectedFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [verificationMatrix, setVerificationMatrix] = useState(null);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [isLoadedFromCache, setIsLoadedFromCache] = useState(false);

    // 1. File Selection with Automatic Background Cache Probing
    async function handleFileSelection(e) {
        const fileList = e.target.files;
        if (!fileList || fileList.length === 0) return;

        const fileObj = fileList[0]; // Isolate the target single file object
        setError("");
        setSelectedFile(fileObj);
        setVerificationMatrix(null);
        setAnalysisResult(null);
        setIsLoadedFromCache(false);

        try {
            setLoading(true);
            const data = await generateHLDMatrix(fileObj);
            if (data.loaded_from_cache) {
                setVerificationMatrix(data.matrix);
                setIsLoadedFromCache(true);
            }
        } catch (err) {
            console.log("Automatic matrix pre-check bypassed or cache miss.", err.message);
        } finally {
            setLoading(false);
        }
    }

    // 2. Manual Matrix Generation (Used for cache misses)
    async function triggerPhase1MatrixIngestion() {
        if (!selectedFile) return;
        setLoading(true);
        setError("");
        setVerificationMatrix(null);

        try {
            const data = await generateHLDMatrix(selectedFile);
            setVerificationMatrix(data.matrix);
            setIsLoadedFromCache(data.loaded_from_cache);
        } catch (err) {
            setError(err.message || "Failed to process document matrix.");
        } finally {
            setLoading(false);
        }
    }

    // 3. Clear Cache and Force Fresh Re-parse
    async function handleForcedCacheClear() {
        if (!selectedFile) return;
        setLoading(true);
        try {
            await clearHLDMatrixCache(selectedFile.name);
            setVerificationMatrix(null);
            setAnalysisResult(null);
            setIsLoadedFromCache(false);
            // Immediately force an explicit fresh re-parse run
            triggerPhase1MatrixIngestion();
        } catch (err) {
            setError(err.message || "Failed to reset backend cache matrix correctly.");
            setLoading(false);
        }
    }

    // 4. Phase-2 Handshake down to Copilot Daemon Session
    async function confirmAndTriggerLLMReview() {
        if (!selectedFile) return;
        setLoading(true);
        setError("");

        try {
            const data = await runCopilotHLDAudit(selectedFile.name);
            setAnalysisResult(data.segmented_blueprint);
        } catch (err) {
            setError(err.message || "Failed running architectural audit analysis.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <section className="hld-analyzer-panel" style={{ padding: "24px", fontFamily: "Segoe UI, sans-serif", display: "grid", gridTemplateColumns: "340px 1fr", gap: "24px" }}>
            
            {/* Left Control Sidebar Column Menu */}
            <div style={{ background: "#fff", padding: "20px", borderRadius: "8px", border: "1px solid #e2e8f0", height: "fit-content", display: "flex", flexDirection: "column", gap: "16px" }}>
                <div>
                    <h3 style={{ margin: "0 0 4px 0", color: "#1e293b" }}>Multi-HLD Portal</h3>
                    <p style={{ margin: 0, fontSize: "0.8rem", color: "#64748b" }}>Isolated sequential document workbench.</p>
                </div>

                <div style={{ background: "#f8fafc", padding: "12px", borderRadius: "6px", border: "1px dashed #cbd5e1" }}>
                    <label style={{ fontWeight: "600", fontSize: "0.85rem", display: "block", marginBottom: "8px" }}>Upload Design Document</label>
                    <input type="file" accept=".pdf,.txt,.html" onChange={handleFileSelection} style={{ fontSize: "0.85rem", width: "100%" }} />
                </div>

                {!verificationMatrix ? (
                    <button onClick={triggerPhase1MatrixIngestion} disabled={loading || !selectedFile} style={{ background: "#0f6cbd", color: "#fff", padding: "10px", border: "none", borderRadius: "6px", fontWeight: "600", cursor: (loading || !selectedFile) ? "not-allowed" : "pointer", opacity: !selectedFile ? 0.6 : 1 }}>
                        {loading ? "Parsing Parameters..." : "🔍 Build Chunk Matrix"}
                    </button>
                ) : (
                    <div style={{ background: "#fef2f2", padding: "12px", borderRadius: "6px", border: "1px solid #fca5a5" }}>
                        <span style={{ fontSize: "0.8rem", color: "#991b1b", display: "block", marginBottom: "8px", fontWeight: "600" }}>⚠️ Matrix Asset Track Active</span>
                        <button onClick={handleForcedCacheClear} disabled={loading} style={{ width: "100%", background: "#dc2626", color: "#fff", padding: "8px", border: "none", borderRadius: "4px", fontSize: "0.85rem", fontWeight: "600", cursor: "pointer" }}>
                            🔄 Reset & Re-parse File Fresh
                        </button>
                    </div>
                )}

                {error && <div style={{ color: "#ef4444", background: "#fef2f2", padding: "10px", borderRadius: "6px", border: "1px solid #fca5a5", fontSize: "0.85rem", fontWeight: "500" }}>{error}</div>}
            </div>

            {/* Right Active Functional Viewport Display Column */}
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                
                {loading && (
                    <div style={{ padding: "40px", background: "#f8fafc", borderRadius: "8px", border: "1px dashed #cbd5e1", textAlign: "center", color: "#64748b", fontWeight: "500" }}>
                        Evaluating document metrics and matrix data configurations... Please hold...
                    </div>
                )}

                {!verificationMatrix && !loading && (
                    <div style={{ background: "#f8fafc", border: "2px dashed #cbd5e1", borderRadius: "8px", padding: "60px", textAlign: "center", color: "#94a3b8" }}>
                        Upload or select an architectural document file to initialize your validation matrix canvas.
                    </div>
                )}

                {/* VIEW 1: Phase-1 Structured Chunk Verification Matrix List Layout */}
                {verificationMatrix && !analysisResult && !loading && (
                    <div style={{ background: "#fff", padding: "20px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", borderBottom: "1px solid #e2e8f0", paddingBottom: "12px" }}>
                            <div>
                                <h3 style={{ margin: 0, color: "#0f6cbd" }}>
                                    Phase-1: Verification Matrix {isLoadedFromCache && <span style={{ fontSize: "0.75rem", background: "#e0f2fe", color: "#0369a1", padding: "2px 8px", borderRadius: "20px", marginLeft: "6px", fontWeight: "600" }}>Auto-Loaded From Disk Cache</span>}
                                </h3>
                                <p style={{ margin: "2px 0 0 0", fontSize: "0.85rem", color: "#64748b" }}>Target Document: <span style={{ fontFamily: "monospace", fontWeight: "600" }}>{selectedFile?.name || "Cached Asset"}</span></p>
                            </div>
                            <button onClick={confirmAndTriggerLLMReview} style={{ background: "#16a34a", color: "#fff", padding: "10px 18px", border: "none", borderRadius: "6px", fontWeight: "700", cursor: "pointer", boxShadow: "0 2px 4px rgba(22,163,74,0.2)" }}>
                                Confirm Matrix & Run Copilot Audit →
                            </button>
                        </div>

                        <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "520px", overflowY: "auto", paddingRight: "6px" }}>
                            {verificationMatrix.map((chunk, idx) => {
                                const hasFocusTags = chunk.metadata.audit_tags.length > 0;
                                return (
                                    <div key={idx} style={{ border: "1px solid #e2e8f0", borderRadius: "6px", padding: "12px", background: hasFocusTags ? "#f8fafc" : "#ffffff", borderLeft: hasFocusTags ? "4px solid #0f6cbd" : "4px solid #cbd5e1" }}>
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                                            <span style={{ fontSize: "0.85rem", fontWeight: "700", color: "#334155" }}>{chunk.metadata.parent_section}</span>
                                            <div style={{ display: "flex", gap: "4px" }}>
                                                {chunk.metadata.audit_tags.map((tag, tIdx) => (
                                                    <span 
                                                        key={tIdx} 
                                                        style={{ 
                                                            fontSize: "0.72rem", 
                                                            background: tag === "SECURITY" ? "#fef2f2" : "#f0fdf4", 
                                                            color: tag === "SECURITY" ? "#ef4444" : "#16a34a", 
                                                            padding: "2px 8px", 
                                                            borderRadius: "4px", 
                                                            fontWeight: "700",
                                                            border: `1px solid ${tag === "SECURITY" ? "#fca5a5" : "#bbf7d0"}`
                                                        }}>{tag}
                                                    </span>
                                                ))}
                                                {chunk.metadata.split_block && <span style={{ fontSize: "0.72rem", background: "#f1f5f9", color: "#475569", padding: "2px 6px", borderRadius: "4px", fontWeight: "500" }}>SPLIT_PARTITION</span>}
                                            </div>
                                        </div>
                                        <details style={{ fontSize: "0.85rem", color: "#475569" }}>
                                            <summary style={{ cursor: "pointer", color: "#0f6cbd", fontWeight: "500" }}>
                                                Expand Source Content Segment View ({chunk.content.split(' ').length} words)
                                            </summary>
                                            <pre style={{ marginTop: "8px", background: "#fafafa", padding: "10px", borderRadius: "4px", fontSize: "0.8rem", whiteSpace: "pre-wrap", overflowX: "auto", border: "1px solid #f1f5f9", fontFamily: "monospace" }}>{chunk.content}</pre>
                                        </details>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* VIEW 1: Phase-1 Structured Chunk Verification Matrix List Layout */}
                {verificationMatrix && !analysisResult && !loading && (
                    <div style={{ background: "#fff", padding: "20px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", borderBottom: "1px solid #e2e8f0", paddingBottom: "12px" }}>
                            <div>
                                <h3 style={{ margin: 0, color: "#0f6cbd" }}>
                                    Phase-1: Verification Matrix {isLoadedFromCache && <span style={{ fontSize: "0.75rem", background: "#e0f2fe", color: "#0369a1", padding: "2px 8px", borderRadius: "20px", marginLeft: "6px", fontWeight: "600" }}>Auto-Loaded From Disk Cache</span>}
                                </h3>
                                <p style={{ margin: "2px 0 0 0", fontSize: "0.85rem", color: "#64748b" }}>Target Document: <span style={{ fontFamily: "monospace", fontWeight: "600" }}>{selectedFile?.name || "Cached Asset"}</span></p>
                            </div>
                            <button onClick={confirmAndTriggerLLMReview} style={{ background: "#16a34a", color: "#fff", padding: "10px 18px", border: "none", borderRadius: "6px", fontWeight: "700", cursor: "pointer", boxShadow: "0 2px 4px rgba(22,163,74,0.2)" }}>
                                Confirm Matrix & Run Copilot Audit →
                            </button>
                        </div>

                        <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "520px", overflowY: "auto", paddingRight: "6px" }}>
                            {verificationMatrix.map((chunk, idx) => {
                                const hasFocusTags = chunk.metadata.audit_tags.length > 0;
                                return (
                                    <div key={idx} style={{ border: "1px solid #e2e8f0", borderRadius: "6px", padding: "12px", background: hasFocusTags ? "#f8fafc" : "#ffffff", borderLeft: hasFocusTags ? "4px solid #0f6cbd" : "4px solid #cbd5e1" }}>
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                                            <span style={{ fontSize: "0.85rem", fontWeight: "700", color: "#334155" }}>{chunk.metadata.parent_section}</span>
                                            <div style={{ display: "flex", gap: "4px" }}>
                                                {chunk.metadata.audit_tags.map((tag, tIdx) => (
                                                    <span 
                                                        key={tIdx} 
                                                        style={{ 
                                                            fontSize: "0.72rem", 
                                                            background: tag === "SECURITY" ? "#fef2f2" : "#f0fdf4", 
                                                            color: tag === "SECURITY" ? "#ef4444" : "#16a34a", 
                                                            padding: "2px 8px", 
                                                            borderRadius: "4px", 
                                                            fontWeight: "700", 
                                                            border: `1px solid ${tag === "SECURITY" ? "#fca5a5" : "#bbf7d0"}`
                                                        }}
                                                    >
                                                        {tag}
                                                    </span>
                                                ))}
                                                {chunk.metadata.split_block && <span style={{ fontSize: "0.72rem", background: "#f1f5f9", color: "#475569", padding: "2px 6px", borderRadius: "4px", fontWeight: "500" }}>SPLIT_PARTITION</span>}
                                            </div>
                                        </div>
                                        <details style={{ fontSize: "0.85rem", color: "#475569" }}>
                                            <summary style={{ cursor: "pointer", color: "#0f6cbd", fontWeight: "500" }}>Expand Source Content Segment View ({chunk.content.split(' ').length} words)</summary>
                                            <pre style={{ marginTop: "8px", background: "#fafafa", padding: "10px", borderRadius: "4px", fontSize: "0.8rem", whiteSpace: "pre-wrap", overflowX: "auto", border: "1px solid #f1f5f9", fontFamily: "monospace" }}>{chunk.content}</pre>
                                        </details>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* VIEW 2: Phase-2 Final Analytical Copilot Output Layout Report Cards Deck */}
                {analysisResult && !loading && (
                    <div style={{ background: "#fff", padding: "20px", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", borderBottom: "1px solid #e2e8f0", paddingBottom: "12px" }}>
                            <div>
                                <h3 style={{ margin: 0, color: "#16a34a" }}>🎯 Phase-2: Isolated Architectural Findings</h3>
                                <p style={{ margin: "2px 0 0 0", fontSize: "0.85rem", color: "#64748b" }}>Target vulnerabilities and integration mismatches extracted via active Copilot SDK session layers.</p>
                            </div>
                            <button onClick={() => setAnalysisResult(null)} style={{ background: "#f1f5f9", border: "1px solid #cbd5e1", padding: "6px 12px", borderRadius: "4px", cursor: "pointer", fontSize: "0.85rem", fontWeight: "600" }}>
                                ← Back to Verification Grid
                            </button>
                        </div>

                        <div style={{ display: "grid", gap: "16px" }}>
                            <div>
                                <h4 style={{ color: "#0f6cbd", margin: "0 0 10px 0" }}>🔍 Code Review Target Sections</h4>
                                {analysisResult.review_required_sections && analysisResult.review_required_sections.length > 0 ? (
                                    analysisResult.review_required_sections.map((sec, idx) => (
                                        <div key={idx} style={{ background: "#fff", border: "1px solid #cbd5e1", padding: "12px", borderRadius: "6px", marginBottom: "8px" }}>
                                            <strong style={{ display: "block", color: "#1e293b", fontSize: "0.9rem" }}>{sec.section_title}</strong>
                                            <p style={{ margin: "4px 0", fontSize: "0.85rem", color: "#475569" }}>{sec.context_summary}</p>
                                            <pre style={{ margin: "6px 0 0 0", background: "#f8fafc", padding: "8px", fontSize: "0.8rem", whiteSpace: "pre-wrap", border: "1px solid #e2e8f0", borderRadius: "4px" }}>{sec.raw_text_content}</pre>
                                        </div>
                                    ))
                                ) : (
                                    <div style={{ fontSize: "0.85rem", fontStyle: "italic", color: "#94a3b8" }}>No critical text alignment violations flags raised.</div>
                                )}
                            </div>

                            <div>
                                <h4 style={{ color: "#16a34a", margin: "10px 0 10px 0" }}>📞 IVR Flow Requirements Profiles</h4>
                                {analysisResult.ivr_flow_requirements && analysisResult.ivr_flow_requirements.length > 0 ? (
                                    analysisResult.ivr_flow_requirements.map((flow, idx) => (
                                        <div key={idx} style={{ background: "#fff", border: "1px solid #cbd5e1", padding: "12px", borderRadius: "6px", marginBottom: "8px" }}>
                                            <strong style={{ display: "block", color: "#1e293b", fontSize: "0.9rem" }}>{flow.flow_name}</strong>
                                            <div style={{ fontSize: "0.82rem", margin: "4px 0", color: "#475569" }}><strong>Trigger Parameter:</strong> {flow.trigger_condition}</div>
                                            <ul style={{ margin: "6px 0 0 0", paddingLeft: "16px", fontSize: "0.85rem", color: "#334155" }}>
                                                {flow.intended_steps?.map((step, sIdx) => <li key={sIdx} style={{ marginBottom: "2px" }}>{step}</li>)}
                                            </ul>
                                        </div>
                                    ))
                                ) : (
                                    <div style={{ fontSize: "0.85rem", fontStyle: "italic", color: "#94a3b8" }}>No functional routing branches documented here.</div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </section>
    );
}