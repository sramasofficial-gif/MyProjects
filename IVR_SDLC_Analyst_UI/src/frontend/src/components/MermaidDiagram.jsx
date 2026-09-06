import { useEffect, useId, useRef, useState } from "react";
import mermaid from "mermaid";

mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "default",
    sequence: {
        useMaxWidth: false,
        wrap: true,
        diagramMarginX: 30,
        diagramMarginY: 20,
        actorMargin: 90,
        width: 180,
        height: 65,
        boxMargin: 10,
        messageMargin: 45,
        noteMargin: 10
    }
});

export default function MermaidDiagram({
    chart,
    title = "Diagram",
    diagramType = "Mermaid Diagram",
    description = "Diagram generated from the selected repository artifact."
}) {
    const containerRef = useRef(null);
    const reactId = useId();
    const [rendering, setRendering] = useState(false);
    const [renderError, setRenderError] = useState("");

    useEffect(() => {
        if (!chart || !containerRef.current) {
            return;
        }

        let cancelled = false;

        async function renderChart() {
            setRendering(true);
            setRenderError("");

            const diagramId = `mermaid-${reactId}-${Date.now()}`.replace(/[^a-zA-Z0-9-_]/g, "");

            try {
                const normalizedChart = chart
                    .replace(/&gt;/g, ">")
                    .replace(/&lt;/g, "<")
                    .replace(/^Flowchart\s+/i, "flowchart ");
                // 1. Pre-validate syntax before injecting to protect canvas stability
                const isValid = await mermaid.parse(normalizedChart);
                if (!isValid) {
                    throw new Error("Mermaid Parser rejected the diagram text structure formatting specifications.");
                }

                console.log("Rendering Mermaid...");
                console.log(chart);

                const { svg, bindFunctions } = await mermaid.render(diagramId, normalizedChart);

                console.log(svg);

                if (cancelled || !containerRef.current) return;

                containerRef.current.innerHTML = svg;
                const renderedSvg =
                    containerRef.current.querySelector("svg");

                if (renderedSvg) {
                    const viewBox =
                        renderedSvg.getAttribute("viewBox");

                    if (viewBox) {
                        const [, , w, h] =
                            viewBox.split(" ");

                        renderedSvg.setAttribute(
                            "width",
                            w
                        );

                        renderedSvg.setAttribute(
                            "height",
                            h
                        );
                    }
                }
                bindFunctions?.(containerRef.current);
            } catch (error) {
                if (cancelled) return;
                console.error("MERMAID PARSING REJECTED GRAPH DEFINITION:", error);
                
                setRenderError(error?.message || "Unable to compile Mermaid syntax properties.");
                if (containerRef.current) containerRef.current.innerHTML = "";
            } finally {
                if (!cancelled) setRendering(false);
            }
        }

        renderChart();
        return () => { cancelled = true; };
    }, [chart, reactId]);

    return (
        <section className="mermaid-panel" style={{ width: "100%", border: "1px solid #d4d4d8", borderRadius: "6px", background: "#fff", padding: "16px" }}>
            <div className="mermaid-panel-header" style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
                <div>
                    <h3 style={{ margin: 0, fontSize: "1.1rem", color: "#18181b" }}>{title}</h3>
                    <p style={{ margin: "4px 0 0 0", fontSize: "0.85rem", color: "#71717a" }}>{description}</p>
                </div>
                <span className="diagram-type-pill" style={{ background: "#e0f2fe", color: "#0369a1", padding: "4px 8px", borderRadius: "12px", fontSize: "0.75rem", fontWeight: "600", height: "fit-content" }}>
                    {diagramType}
                </span>
            </div>

            {rendering && <div style={{ padding: "20px", color: "#0f6cbd", fontSize: "0.9rem" }}><span className="loading-spinner" /> Drawing vector graph nodes...</div>}

            {renderError && (
                <div className="diagram-error" role="alert" style={{ background: "#fef2f2", border: "1px solid #fca5a5", color: "#991b1b", padding: "12px", borderRadius: "4px", margin: "10px 0" }}>
                    <strong>Diagram Layout Compilation Failed:</strong>
                    <p style={{ margin: "4px 0", fontSize: "0.85rem" }}>{renderError}</p>
                    <details style={{ marginTop: "8px", background: "#fff", padding: "6px", borderRadius: "4px", border: "1px solid #fee2e2" }}>
                        <summary style={{ fontSize: "0.8rem", cursor: "pointer" }}>View raw structure code input sent by AI engine</summary>
                        <pre style={{ margin: "6px 0 0 0", fontSize: "0.8rem", overflowX: "auto", background: "#fafafa", padding: "6px" }}>{chart}</pre>
                    </details>
                </div>
            )}

            <div className="mermaid-scroll-container" style={{ overflowX: "auto", width: "100%" }}>
                <div ref={containerRef} className="diagram-canvas" aria-label={title} />
            </div>
        </section>
    );
}
