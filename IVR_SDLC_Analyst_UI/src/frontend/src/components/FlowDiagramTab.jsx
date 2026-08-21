import {
    useMemo,
    useState
} from "react";

import MermaidDiagram
    from "./MermaidDiagram";

import {
    contactFlowToSequenceDiagram
} from "../utils/contactFlowToSequence";

import {
    lambdaToSequence
} from "../utils/lambdaToSequence";

import {
    lambdaToFlowchart
} from "../utils/lambdaToFlowchart";

import {
    lambdaToDependencyGraph
} from "../utils/lambdaToDependencyGraph";


function isContactFlowFile(path) {
    if (!path) {
        return false;
    }

    const normalizedPath =
        path
            .replaceAll("\\", "/")
            .toLowerCase();

    return (
        normalizedPath.startsWith(
            "contact-flows/"
        ) &&
        normalizedPath.endsWith(".json")
    );
}


function isLambdaFile(path) {
    if (!path) {
        return false;
    }

    const normalizedPath =
        path
            .replaceAll("\\", "/")
            .toLowerCase();

    return (
        normalizedPath.startsWith("lambda/") &&
        (
            normalizedPath.endsWith(".ts") ||
            normalizedPath.endsWith(".js") ||
            normalizedPath.endsWith(".mjs")
        )
    );
}


function getLambdaDiagramMetadata(
    lambdaDiagramType
) {
    switch (lambdaDiagramType) {
        case "sequence":
            return {
                title:
                    "Lambda Sequence Diagram",
                diagramType:
                    "Sequence Diagram",
                description:
                    "Runtime interaction view derived from awaited calls in the selected Lambda file."
            };

        case "flowchart":
            return {
                title:
                    "Lambda Execution Flow",
                diagramType:
                    "Execution Flow",
                description:
                    "Execution path derived from the selected Lambda file."
            };

        case "dependency":
        default:
            return {
                title:
                    "Lambda Dependency Graph",
                diagramType:
                    "Dependency Graph",
                description:
                    "Module and service dependencies derived from the selected Lambda file."
            };
    }
}


export default function FlowDiagramTab({
    selectedFile,
    content,
    loading,
    error
}) {
    const [
        lambdaDiagramType,
        setLambdaDiagramType
    ] = useState("dependency");

    const isContactFlow =
        isContactFlowFile(selectedFile);

    const isLambda =
        isLambdaFile(selectedFile);

    const diagramResult =
        useMemo(() => {
            if (
                !selectedFile ||
                !content ||
                loading ||
                error
            ) {
                return {
                    chart: "",
                    title: "",
                    diagramType: "",
                    description: "",
                    generationError: ""
                };
            }

            console.info(
                `[${new Date().toISOString()}]`,
                "DIAGRAM GENERATION START",
                {
                    selectedFile,
                    lambdaDiagramType
                }
            );

            try {
                if (isContactFlow) {
                    const chart =
                        contactFlowToSequenceDiagram(
                            content,
                            selectedFile
                        );

                    console.info(
                        `[${new Date().toISOString()}]`,
                        "CONTACT FLOW DIAGRAM GENERATED",
                        selectedFile
                    );

                    return {
                        chart,
                        title:
                            "Contact Flow Sequence Diagram",
                        diagramType:
                            "Sequence Diagram",
                        description:
                            "Runtime interaction view derived from the selected contact flow.",
                        generationError: ""
                    };
                }

                if (isLambda) {
                    const metadata =
                        getLambdaDiagramMetadata(
                            lambdaDiagramType
                        );

                    let chart = "";

                    switch (lambdaDiagramType) {
                        case "sequence":
                            chart =
                                lambdaToSequence(
                                    content,
                                    selectedFile
                                );
                            break;

                        case "flowchart":
                            chart =
                                lambdaToFlowchart(
                                    content,
                                    selectedFile
                                );
                            break;

                        case "dependency":
                        default:

                            console.log(
                                "Generating Dependency Diagram",
                                selectedFile
                            );

                            chart =
                                lambdaToDependencyGraph(
                                    content,
                                    selectedFile
                                );
                            break;
                    }

                    console.info(
                        `[${new Date().toISOString()}]`,
                        "LAMBDA DIAGRAM GENERATED",
                        {
                            selectedFile,
                            lambdaDiagramType
                        }
                    );

                    return {
                        chart,
                        ...metadata,
                        generationError: ""
                    };
                }

                return {
                    chart: "",
                    title: "",
                    diagramType: "",
                    description: "",
                    generationError: ""
                };
            } catch (generationError) {
                console.error(
                    `[${new Date().toISOString()}]`,
                    "DIAGRAM GENERATION FAILED",
                    {
                        selectedFile,
                        lambdaDiagramType,
                        generationError
                    }
                );

                return {
                    chart: "",
                    title: "",
                    diagramType: "",
                    description: "",
                    generationError:
                        generationError?.message ||
                        "Unable to generate the diagram."
                };
            }
        }, [
            selectedFile,
            content,
            loading,
            error,
            isContactFlow,
            isLambda,
            lambdaDiagramType
        ]);

    if (!isContactFlow && !isLambda) {
        return (
            <section className="flow-diagram-tab">

                <div className="content-heading">
                    <div>
                        <h2>Diagram</h2>

                        <div className="selected-path">
                            {selectedFile}
                        </div>
                    </div>
                </div>

                <div className="info-message">
                    <strong>
                        Diagrams are available for:
                    </strong>

                    <ul>
                        <li>
                            Contact-flow JSON files under
                            the contact-flows folder
                        </li>

                        <li>
                            TypeScript or JavaScript files
                            under the lambda folder
                        </li>
                    </ul>
                </div>

            </section>
        );
    }

    if (loading) {
        return (
            <section className="flow-diagram-tab">

                <div className="content-heading">
                    <div>
                        <h2>Diagram</h2>

                        <div className="selected-path">
                            {selectedFile}
                        </div>
                    </div>
                </div>

                <div className="loading-message">
                    <span className="loading-spinner" />

                    Loading selected file content...
                </div>

            </section>
        );
    }

    if (error) {
        return (
            <section className="flow-diagram-tab">

                <div className="content-heading">
                    <div>
                        <h2>Diagram</h2>

                        <div className="selected-path">
                            {selectedFile}
                        </div>
                    </div>
                </div>

                <div
                    className="error-message"
                    role="alert"
                >
                    <strong>
                        Unable to load the selected file.
                    </strong>

                    <span>{error}</span>
                </div>

            </section>
        );
    }

    if (!content) {
        return (
            <section className="flow-diagram-tab">

                <div className="content-heading">
                    <div>
                        <h2>Diagram</h2>

                        <div className="selected-path">
                            {selectedFile}
                        </div>
                    </div>
                </div>

                <div className="info-message">
                    The selected file does not contain
                    diagrammable content.
                </div>

            </section>
        );
    }

    return (
        <section className="flow-diagram-tab">

            <div className="diagram-page-header">

                <div>
                    <h2>Diagram</h2>

                    <div className="selected-path">
                        {selectedFile}
                    </div>
                </div>

                {isLambda && (
                    <div className="diagram-tabs">

                        <button
                            className={
                                lambdaDiagramType === "dependency"
                                    ? "diagram-tab active"
                                    : "diagram-tab"
                            }
                            onClick={() =>
                                setLambdaDiagramType(
                                    "dependency"
                                )
                            }
                        >
                            Dependency Graph
                        </button>

                        <button
                            className={
                                lambdaDiagramType === "flowchart"
                                    ? "diagram-tab active"
                                    : "diagram-tab"
                            }
                            onClick={() =>
                                setLambdaDiagramType(
                                    "flowchart"
                                )
                            }
                        >
                            Execution Flow
                        </button>

                        <button
                            className={
                                lambdaDiagramType === "sequence"
                                    ? "diagram-tab active"
                                    : "diagram-tab"
                            }
                            onClick={() =>
                                setLambdaDiagramType(
                                    "sequence"
                                )
                            }
                        >
                            Sequence Diagram
                        </button>

                    </div>
                )}

            </div>

            {diagramResult.generationError && (
                <div
                    className="error-message"
                    role="alert"
                >
                    <strong>
                        Unable to generate the diagram.
                    </strong>

                    <span>
                        {
                            diagramResult
                                .generationError
                        }
                    </span>
                </div>
            )}

            {!diagramResult.generationError &&
                diagramResult.chart && (
                    <MermaidDiagram
                        chart={diagramResult.chart}
                        title={diagramResult.title}
                        diagramType={
                            diagramResult.diagramType
                        }
                        description={
                            diagramResult.description
                        }
                    />
                )}

            {!diagramResult.generationError &&
                !diagramResult.chart && (
                    <div className="info-message">
                        No diagram data was detected in
                        the selected file.
                    </div>
                )}

        </section>
    );
}
