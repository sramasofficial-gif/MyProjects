import { useEffect, useState, useRef } from "react";
import MermaidDiagram from "./MermaidDiagram";
import { requestDiagramGeneration } from "../services/api";
import { contactFlowToSequenceDiagram } from "../utils/contactFlowToSequence";

export default function FlowDiagramTab({ selectedFile, content, loading, error }) {
    const [lambdaDiagramType, setLambdaDiagramType] = useState("dependency");
    const [chartData, setChartData] = useState("");
    const [generationLoading, setGenerationLoading] = useState(false);
    const [generationError, setGenerationError] = useState("");
    const [diagramCache, setDiagramCache] = useState({});
    
    // 🟢 Critical Lock tracking ref to block duplicate concurrent requests completely
    const pendingRequestRef = useRef(null);

    const normalizedPath = (selectedFile || "").replaceAll("\\", "/").toLowerCase();
    const isContactFlow = normalizedPath.startsWith("contact-flows/") && normalizedPath.endsWith(".json");
    const isLambda = normalizedPath.startsWith("lambda/") && 
        (normalizedPath.endsWith(".ts") || normalizedPath.endsWith(".js") || normalizedPath.endsWith(".mjs"));

    useEffect(() => {
        if (!selectedFile || !content || loading || error) {
            setChartData("");
            return;
        }

        if (isContactFlow) {
            try {
                const chart = contactFlowToSequenceDiagram(content, selectedFile);
                setChartData(chart);
                setGenerationError("");
            } catch (err) {
                setGenerationError(err.message || "Failed to generate contact flow diagram.");
            }
            return;
        }

        if (isLambda) {
            let isCancelled = false;
            const cacheKey = `${selectedFile}::${content.length}::${lambdaDiagramType}`;

            if (diagramCache[cacheKey]) {
                setChartData(diagramCache[cacheKey]);
                setGenerationError("");
                return;
            }

            // 🟢 BLOCK DUPLICATE CONCURRENT TRIGGERS
            if (pendingRequestRef.current === cacheKey) {
                return; 
            }

            // 🟢 Update the fetchRemoteBlueprint logic inside your FlowDiagramTab.jsx file

            async function fetchRemoteBlueprint() {
                pendingRequestRef.current = cacheKey;
                setGenerationLoading(true);
                setGenerationError("");
                try {
                    const result = await requestDiagramGeneration(selectedFile, content, lambdaDiagramType);
                    
                    if (!isCancelled) {
                        // 'result' is now guaranteed to be the clean raw text string array from Step 1
                        const mermaidStr = typeof result === "string" ? result : (result?.mermaid_string || "");
                        
                        // 🛑 DEBUG CHECK: Open your F12 browser console to verify this text prints clean!
                        console.log("--- GRAPH CORE CODE RECEIVED FROM BACKEND ---");
                        console.log(mermaidStr);
                        
                        if (!mermaidStr.trim()) {
                            throw new Error("The backend returned an empty diagram string text payload.");
                        }

                        setGenerationError("");
                        setDiagramCache(prev => ({ ...prev, [cacheKey]: mermaidStr }));
                        setChartData(mermaidStr);
                    }
                } catch (err) {
                    if (!isCancelled) {
                        setChartData("");
                        setGenerationError(err.message || "Unable to download layout blueprints.");
                    }
                } finally {
                    if (!isCancelled) {
                        setGenerationLoading(false);
                        if (pendingRequestRef.current === cacheKey) {
                            pendingRequestRef.current = null;
                        }
                    }
                }
            }

            fetchRemoteBlueprint();
            return () => { 
                isCancelled = true;
                if (pendingRequestRef.current === cacheKey) {
                    pendingRequestRef.current = null;
                }
            };
        }
    }, [selectedFile, content, loading, error, lambdaDiagramType, isContactFlow, isLambda]);

    if (!loading && !generationLoading && !isContactFlow && !isLambda) {
        return (
            <section className="flow-diagram-tab">
                <div className="diagram-page-header">
                    <div><h2>Diagram</h2><div className="selected-path">{selectedFile}</div></div>
                </div>
                <div className="info-message">
                    <strong>Diagrams are available for files under contact-flows/ or lambda/ paths.</strong>
                </div>
            </section>
        );
    }

    const getMetadata = () => {
        if (lambdaDiagramType === "flowchart") return { title: "Lambda Execution Flow", type: "Execution Flow", desc: "Detailed step-by-step logic path." };
        if (lambdaDiagramType === "sequence") return { title: "Lambda Sequence Diagram", type: "Sequence Diagram", desc: "Runtime execution lifelines." };
        return { title: "Lambda Dependency Graph", type: "Dependency Graph", desc: "Module and service dependencies." };
    };
    const meta = getMetadata();

    return (
        <section className="flow-diagram-tab">
            <div className="diagram-page-header">
                <div><h2>Diagram</h2><div className="selected-path">{selectedFile}</div></div>
                {isLambda && !loading && (
                    <div className="diagram-tabs">
                        <button className={lambdaDiagramType === "dependency" ? "diagram-tab active" : "diagram-tab"} onClick={() => setLambdaDiagramType("dependency")}>Dependency Graph</button>
                        <button className={lambdaDiagramType === "flowchart" ? "diagram-tab active" : "diagram-tab"} onClick={() => setLambdaDiagramType("flowchart")}>Execution Flow</button>
                        <button className={lambdaDiagramType === "sequence" ? "diagram-tab active" : "diagram-tab"} onClick={() => setLambdaDiagramType("sequence")}>Sequence Diagram</button>
                    </div>
                )}
            </div>

            {(loading || generationLoading) && (
                <div className="diagram-loading" style={{ padding: "20px", color: "#0f6cbd" }}>
                    <span className="loading-spinner" style={{ marginRight: "10px" }} />
                    Assembling high-fidelity codebase blueprints via backend services...
                </div>
            )}

            {generationError && (
                <div className="diagram-error" role="alert" style={{ padding: "20px", color: "#ef4444" }}>
                    <strong>Diagram rendering failed:</strong> <p>{generationError}</p>
                </div>
            )}

            {!loading && !generationLoading && chartData && (
                <MermaidDiagram
                    chart={chartData}
                    title={isContactFlow ? "Contact Flow Sequence" : meta.title}
                    diagramType={isContactFlow ? "Sequence Diagram" : meta.type}
                    description={isContactFlow ? "Runtime view derived from selected contact flow." : meta.desc}
                />
            )}
        </section>
    );
}
