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
        useMaxWidth: true,
        wrap: true,
        diagramMarginX: 30,
        diagramMarginY: 20,
        actorMargin: 70,
        width: 180,
        height: 65,
        boxMargin: 10,
        messageMargin: 40,
        noteMargin: 10
    },
    themeVariables: {
        fontFamily:
            "Segoe UI, Arial, sans-serif",
        primaryColor: "#f8fafc",
        primaryTextColor: "#172b4d",
        primaryBorderColor: "#0f6cbd",
        lineColor: "#64748b",
        secondaryColor: "#eff6ff",
        tertiaryColor: "#f8fafc",
        actorBkg: "#f8fafc",
        actorBorder: "#0f6cbd",
        actorTextColor: "#172b4d",
        actorLineColor: "#94a3b8",
        signalColor: "#334155",
        signalTextColor: "#172b4d",
        labelBoxBkgColor: "#eff6ff",
        labelBoxBorderColor: "#93c5fd",
        labelTextColor: "#172b4d",
        loopTextColor: "#172b4d",
        noteBkgColor: "#fff7d6",
        noteBorderColor: "#f59e0b",
        noteTextColor: "#713f12"
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