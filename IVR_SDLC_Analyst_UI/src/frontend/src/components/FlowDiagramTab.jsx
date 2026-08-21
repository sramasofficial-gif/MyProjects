import {
    useMemo,
    useState
} from "react";

import MermaidDiagram
    from "./MermaidDiagram";

import {
    contactFlowToSequenceDiagram
} from "../utils/contactFlowToSequence";

const SAMPLE_SEQUENCE = `
sequenceDiagram
    autonumber
    actor Caller
    participant Flow as cfAccountStatus
    participant SSM as GetSsmParams
    participant Lookup as Account Lookup Module
    participant Status as GetAccountStatus
    participant Summary as GetAccountSummaryInfo
    participant Data as AgencyCodeConfig Table

    Caller->>Flow: Start contact flow
    activate Flow

    Flow->>SSM: Load prompt defaults
    SSM-->>Flow: Prompt config

    Flow->>Lookup: Invoke account lookup
    Lookup-->>Flow: Lookup result

    Flow->>Status: Get account status
    Status-->>Flow: statusCode + account data

    Flow->>Summary: Get account summary info
    Summary-->>Flow: Account summary

    Flow->>Data: Lookup agency code config
    Data-->>Flow: externalNumber1 / externalNumber2 / isActive

    Flow->>Flow: Evaluate status, CPC, agency, and active status

    alt Fraud case
        Flow->>Flow: Route to FRD queue
    else Agency or queue routing
        Flow->>Flow: Route to appropriate queue or flow
    else Invalid input or retry
        Flow->>Flow: Loop or transfer to error handling
    end

    Flow-->>Caller: Play prompt, transfer, or disconnect
    deactivate Flow
`;

function isContactFlowFile(path) {
    if (!path) {
        return false;
    }

    const normalized =
        path
            .replaceAll("\\", "/")
            .toLowerCase();

    return (
        normalized.startsWith(
            "contact-flows/"
        ) &&
        normalized.endsWith(".json")
    );
}

export default function FlowDiagramTab({
    selectedFile,
    content,
    loading,
    error
}) {
    const [showSource, setShowSource] =
        useState(false);

    const result = useMemo(() => {
        if (
            !selectedFile ||
            !isContactFlowFile(selectedFile) ||
            !content
        ) {
            return {
                chart: "",
                conversionError: ""
            };
        }

        console.info(
            `[${new Date().toISOString()}]`,
            "SEQUENCE CONVERSION START",
            selectedFile
        );

        try {
            const chart =
                contactFlowToSequenceDiagram(
                    content,
                    selectedFile
                );

            console.info(
                `[${new Date().toISOString()}]`,
                "SEQUENCE CONVERSION END",
                selectedFile
            );

            return {
                chart,
                conversionError: ""
            };
        } catch (conversionError) {
            console.error(
                `[${new Date().toISOString()}]`,
                "SEQUENCE CONVERSION FAILED",
                selectedFile,
                conversionError
            );

            return {
                chart: "",
                conversionError:
                    conversionError?.message ||
                    "Unable to convert the contact flow."
            };
        }
    }, [content, selectedFile]);

    if (!isContactFlowFile(selectedFile)) {
        return (
            <section>
                <div className="content-heading">
                    <div>
                        <h2>Flow Diagram</h2>

                        <div className="selected-path">
                            {selectedFile}
                        </div>
                    </div>
                </div>

                <div className="info-message">
                    Sequence Diagram is available
                    for JSON files under the
                    contact-flows folder.
                </div>
            </section>
        );
    }

    if (loading) {
        return (
            <div className="loading-message">
                <span className="loading-spinner" />
                Loading the selected contact flow...
            </div>
        );
    }

    if (error) {
        return (
            <div
                className="error-message"
                role="alert"
            >
                <strong>
                    Unable to load the contact flow.
                </strong>

                <span>{error}</span>
            </div>
        );
    }

    if (result.conversionError) {
        return (
            <div
                className="error-message"
                role="alert"
            >
                <strong>
                    Unable to generate the
                    sequence diagram.
                </strong>

                <span>
                    {result.conversionError}
                </span>
            </div>
        );
    }

    return (
        <section className="flow-diagram-tab">

            <div className="diagram-toolbar">

                <div>
                    <h2>Flow Diagram</h2>

                    <div className="selected-path">
                        {selectedFile}
                    </div>
                </div>

                <button
                    type="button"
                    className="diagram-source-button"
                    onClick={() =>
                        setShowSource(previous =>
                            !previous
                        )
                    }
                >
                    {showSource
                        ? "Hide Mermaid Source"
                        : "View Mermaid Source"}
                </button>

            </div>

            <MermaidDiagram
                chart={SAMPLE_SEQUENCE}
                title="Contact Flow Sequence Diagram"
            />

            {showSource && (
                <div className="mermaid-source-card">

                    <div className="viewer-header">
                        Mermaid Source
                    </div>

                    <pre>
                        {result.chart}
                    </pre>

                </div>
            )}

        </section>
    );
}