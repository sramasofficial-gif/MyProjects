import {
    useEffect,
    useId,
    useRef,
    useState
} from "react";

import mermaid from "mermaid";

mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "default",
    sequence: {
        useMaxWidth: false, // Keep false to allow natural browser scrolling
        wrap: true,
        diagramMarginX: 30,
        diagramMarginY: 20,
        actorMargin: 90,    // 🟢 Slightly increased for better spacing
        width: 180,
        height: 65,
        boxMargin: 10,
        messageMargin: 45,  // 🟢 More breathing room for arrow text descriptions
        noteMargin: 10
    },
    themeVariables: {
        fontFamily: "Segoe UI, -apple-system, Arial, sans-serif",
        
        // 🟢 Actor Box Colors (CodeToFlow uses crisp, muted modern boxes)
        actorBkg: "#f4f4f5",
        actorBorder: "#d4d4d8",
        actorTextColor: "#18181b",
        actorLineColor: "#a1a1aa", // Cleaner timeline stems
        
        // 🟢 Message Arrows & Text
        signalColor: "#27272a",
        signalTextColor: "#3f3f46",
        
        // 🟢 Active Execution Bars (The lifelines spawned by our new script)
        activationBkg: "#e4e4e7",
        activationBorder: "#71717a",
        
        // 🟢 Note blocks configuration styling parameters
        noteBkgColor: "#27272a",   // Shaded dark notes look great against bright stems
        noteBorderColor: "#18181b",
        noteTextColor: "#ffffff",
        
        // 🟢 Loop block controls
        loopTextColor: "#18181b",
        labelBoxBkgColor: "#f4f4f5",
        labelBoxBorderColor: "#d4d4d8",
        labelTextColor: "#18181b"
    }
});

export default function MermaidDiagram({
    chart,
    title = "Diagram",
    diagramType = "Mermaid Diagram",
    description =
        "Diagram generated from the selected repository artifact."
}) {
    const containerRef = useRef(null);
    const reactId = useId();

    const [rendering, setRendering] =
        useState(false);

    const [renderError, setRenderError] =
        useState("");

    useEffect(() => {
        if (!chart || !containerRef.current) {
            return;
        }

        let cancelled = false;

        async function renderChart() {
            setRendering(true);
            setRenderError("");

            const diagramId =
                `mermaid-${reactId}-${Date.now()}`
                    .replace(/[^a-zA-Z0-9-_]/g, "");

            console.info(
                `[${new Date().toISOString()}]`,
                "MERMAID RENDER START",
                diagramId
            );

            try {
                const { svg, bindFunctions } =
                    await mermaid.render(
                        diagramId,
                        chart
                    );

                if (
                    cancelled ||
                    !containerRef.current
                ) {
                    return;
                }

                containerRef.current.innerHTML =
                    svg;

                bindFunctions?.(
                    containerRef.current
                );

                console.info(
                    `[${new Date().toISOString()}]`,
                    "MERMAID RENDER END",
                    diagramId
                );
            } catch (error) {
                if (cancelled) {
                    return;
                }

                console.error(
                    `[${new Date().toISOString()}]`,
                    "MERMAID RENDER FAILED",
                    error
                );

                setRenderError(
                    error?.message ||
                    "Unable to render the Mermaid diagram."
                );

                if (containerRef.current) {
                    containerRef.current.innerHTML =
                        "";
                }
            } finally {
                if (!cancelled) {
                    setRendering(false);
                }
            }
        }

        renderChart();

        return () => {
            cancelled = true;
        };
    }, [chart, reactId]);

    return (
        <section className="mermaid-panel">

            <div className="mermaid-panel-header">

                <div>
                    <h2 className="mermaid-title">
                        {title}
                    </h2>

                    <p className="mermaid-subtitle">
                        {description}
                    </p>
                </div>

                <span className="diagram-type-pill">
                    {diagramType}
                </span>

            </div>

            {rendering && (
                <div className="diagram-loading">
                    <span className="loading-spinner" />
                    Rendering {diagramType.toLowerCase()}...
                </div>
            )}

            {renderError && (
                <div
                    className="diagram-error"
                    role="alert"
                >
                    <strong>
                        Diagram rendering failed.
                    </strong>

                    <span>{renderError}</span>
                </div>
            )}

            <div className="mermaid-scroll-container">

                <div
                    ref={containerRef}
                    className="diagram-canvas"
                    aria-label={title}
                />

            </div>

            {renderError && (
                <details className="mermaid-source-panel">
                    <summary>
                        View Mermaid source
                    </summary>

                    <pre>{chart}</pre>
                </details>
            )}

        </section>
    );
}