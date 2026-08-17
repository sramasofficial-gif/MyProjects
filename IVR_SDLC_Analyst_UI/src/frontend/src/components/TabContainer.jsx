import {
    useCallback,
    useEffect,
    useState
} from "react";

import {
    loadFile,
    auditFlow,
    requestLambdaReview
} from "../services/api";


const tabs = [
    {
        id: "dashboard",
        label: "Dashboard"
    },
    {
        id: "flow",
        label: "Flow Analysis"
    },
    {
        id: "review",
        label: "Review Report"
    },
    {
        id: "diagram",
        label: "Flow Diagram"
    },
    {
        id: "chat",
        label: "Chat"
    }
];


function isContactFlowFile(path) {
    if (!path) return false;
    const normalizedPath = path.replaceAll("\\", "/").toLowerCase();
    return (
        normalizedPath.startsWith("contact-flows/") &&
        normalizedPath.endsWith(".json")
    );
}

function isLambdaFile(path) {
    if (!path) return false;
    const normalizedPath = path.replaceAll("\\", "/").toLowerCase();
    return (
        normalizedPath.startsWith("lambda/") &&
        (normalizedPath.endsWith(".ts") || 
         normalizedPath.endsWith(".js") || 
         normalizedPath.endsWith(".mjs"))
    );
}


export default function TabContainer({
    selectedFile
}) {
    const [activeTab, setActiveTab] =
        useState("dashboard");

    const [content, setContent] =
        useState("");

    const [contentLoading, setContentLoading] =
        useState(false);

    const [contentError, setContentError] =
        useState("");

    const [auditReport, setAuditReport] =
        useState(null);

    const [auditLoading, setAuditLoading] =
        useState(false);

    const [auditCache, setAuditCache] = useState({});

    const [auditError, setAuditError] =
        useState("");

    const [lastAuditedAt, setLastAuditedAt] =
        useState(null);

    const [reviewReport, setReviewReport] =
        useState(null);

    const [reviewCache, setReviewCache] = useState({});
    
    // inside TabContainer.jsx active tab conditional effects block:
    //const [lambdaReview, setLambdaReview] = useState("");

    const [reviewLoading, setReviewLoading] =
        useState(false);

    const [reviewError, setReviewError] =
        useState("");

    const [lastReviewedAt, setLastReviewedAt] =
        useState(null);


    const runAudit = useCallback(
        async (path) => {
            if (!isContactFlowFile(path)) {
                setAuditReport(null);
                setAuditError("");
                setLastAuditedAt(null);
                return;
            }

            setAuditLoading(true);
            setAuditError("");

            try {
                const report =
                    await auditFlow(path);

                setAuditCache(prev => ({
                    ...prev,
                    [path]: report
                }));

                setAuditReport(report);
                setLastAuditedAt(new Date());
            } catch (error) {
                console.error(
                    "Flow audit failed:",
                    error
                );

                setAuditReport(null);
                setAuditError(
                    error.message ||
                    "Unable to run the flow audit."
                );
            } finally {
                setAuditLoading(false);
            }
        },
        []
    );

    useEffect(() => {

        if (!selectedFile) {

            setAuditReport(null);
            setReviewReport(null);

            return;
        }

        if (!isContactFlowFile(selectedFile)) {

            setAuditReport(null);
            setAuditError("");

        }

        if (!isLambdaFile(selectedFile)) {

            setReviewReport(null);
            setReviewError("");

        }

    }, [selectedFile]);

    useEffect(() => {

        if (!selectedFile) {

            setContent("");
            setContentError("");

            return;
        }

        let cancelled = false;

        async function loadSelectedFile() {

            setContentLoading(true);
            setContentError("");

            try {

                const result =
                    await loadFile(selectedFile);

                if (!cancelled) {

                    setContent(
                        result.content || ""
                    );

                }

            } catch (err) {

                if (!cancelled) {

                    setContentError(
                        err?.message ||
                        "Unable to load file."
                    );

                }

            } finally {

                if (!cancelled) {

                    setContentLoading(false);

                }

            }

        }

        loadSelectedFile();

        return () => {

            cancelled = true;

        };

    }, [selectedFile]);

    useEffect(() => {

        if (
            !selectedFile ||
            !isContactFlowFile(selectedFile)
        ) {
            return;
        }

        if (auditCache[selectedFile]) {

            setAuditReport(
                auditCache[selectedFile]
            );

            return;
        }

        handleRefreshAudit();

    }, [selectedFile, auditCache]);

    useEffect(() => {

        if (
            !selectedFile ||
            !isLambdaFile(selectedFile)
        ) {
            return;
        }

        // already cached
        if (reviewCache[selectedFile]) {
            setReviewReport(
                reviewCache[selectedFile]
            );

            return;
        }

        handleRefreshReview();

    }, [selectedFile, reviewCache]);


    function handleRefreshAudit() {
        if (!selectedFile || auditLoading) {
            return;
        }

        runAudit(selectedFile);
    }

    async function handleRefreshReview() {

        if (!selectedFile) return;

        setReviewLoading(true);
        setReviewError("");

        try {

            const result =
                await requestLambdaReview(selectedFile);

            setReviewCache(prev => ({
                ...prev,
                [selectedFile]: result
            }));

            setLastReviewedAt(new Date());

            setReviewReport(result);

        } catch (err) {

            setReviewError(
                err?.message ||
                "Review execution failed."
            );

        } finally {

            setReviewLoading(false);

        }
    }

    return (
        <div className="main-panel">

            <div
                className="tabs"
                role="tablist"
                aria-label="Analysis views"
            >
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        type="button"
                        role="tab"
                        aria-selected={
                            activeTab === tab.id
                        }
                        className={
                            activeTab === tab.id
                                ? "tab active"
                                : "tab"
                        }
                        onClick={() =>
                            setActiveTab(tab.id)
                        }
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            <div className="tab-content">

                {!selectedFile && (
                    <EmptySelection />
                )}

                {selectedFile &&
                    activeTab === "dashboard" && (
                        <DashboardTab
                            selectedFile={selectedFile}
                            content={content}
                            loading={contentLoading}
                            error={contentError}
                            auditReport={auditReport}
                            auditLoading={auditLoading}
                            reviewReport={reviewReport}
                        />
                    )}

                {selectedFile &&
                    activeTab === "flow" && (
                        <FlowAuditTab
                            selectedFile={selectedFile}
                            report={auditReport}
                            loading={auditLoading}
                            error={auditError}
                            lastAuditedAt={
                                lastAuditedAt
                            }
                            onRefresh={
                                handleRefreshAudit
                            }
                        />
                    )}

                {selectedFile &&
                    activeTab === "review" && (
                        <div className="copilot-review-workspace" style={{ padding: "5px" }}>
                            {!isLambdaFile(selectedFile) ? (
                                <PlaceholderTab 
                                    title="Review Engine Information" 
                                    message="Select an AWS Lambda function file (.ts, .js, .mjs) under the lambda/ folder tree to execute automated GitHub Copilot audits." 
                                />
                            ) : (
                                <div className="file-viewer-card" style={{ padding: "20px", background: "#fff", border: "1px solid #ddd", borderRadius: "6px" }}>
                                    <div className="viewer-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", borderBottom: "2px solid #f4f4f4", paddingBottom: "10px" }}>
                                        <h2 style={{ margin: 0, fontSize: "18px", color: "#24292e", display: "flex", alignItems: "center", gap: "8px" }}>
                                            🤖 GitHub Copilot Infrastructure Review
                                        </h2>
                                        <button
                                            className="refresh-button"
                                            onClick={handleRefreshReview}
                                            disabled={reviewLoading}
                                        >
                                            {reviewLoading
                                                ? "Running..."
                                                : "🔄 Refresh Review"}
                                        </button>
                                        {lastReviewedAt && !reviewLoading && (
                                            <div className="audit-timestamp">
                                                Last reviewed:
                                                {" "}
                                                {lastReviewedAt.toLocaleString()}
                                            </div>
                                        )}

                                        {reviewReport?.overallRisk && (
                                            <span className={`status-badge ${
                                                reviewReport.overallRisk === "High" ? "status-fail" : reviewReport.overallRisk === "Medium" ? "assessment-warning" : "status-pass"
                                            }`} style={{ padding: "4px 10px", borderRadius: "4px", fontSize: "12px", fontWeight: "bold" }}>
                                                Risk Level: {reviewReport.overallRisk}
                                            </span>
                                        )}
                                    </div>

                                    {reviewLoading && <LoadingMessage message="Querying corporate GitHub Copilot analyzer execution streams..." />}
                                    {reviewError && <ErrorMessage message={reviewError} />}

                                    {!reviewLoading && reviewReport && reviewReport.success === false && (
                                        <ErrorMessage message={reviewReport.message || "The Copilot validation routine dropped with exceptions."} />
                                    )}

                                    {!reviewLoading && reviewReport && reviewReport.success !== false && (
                                        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                                            
                                            {/* Summary Text Panel Context */}
                                            <div style={{ background: "#f6f8fa", padding: "15px", borderRadius: "6px", borderLeft: "4px solid #0366d6", fontSize: "14px", lineHeight: "1.5", color: "#24292e" }}>
                                                <strong>Executive Summary:</strong> {reviewReport.summary || "No high-level overview was provided by the evaluation model."}
                                            </div>

                                            {/* Recommendations Data Table Grid */}
                                            <div>
                                                <h3 style={{ fontSize: "14px", marginBottom: "10px", color: "#586069", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                                                    Structured Code Findings ({reviewReport.recommendations?.length || 0})
                                                </h3>
                                                
                                                {(!reviewReport.recommendations || reviewReport.recommendations.length === 0) ? (
                                                    <div className="info-message">No structural optimization findings observed in the codebase manifest.</div>
                                                ) : (
                                                    <div style={{ overflowX: "auto", border: "1px solid #e1e4e8", borderRadius: "6px" }}>
                                                        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "13px" }}>
                                                            <thead>
                                                                <tr style={{ background: "#f6f8fa", borderBottom: "1px solid #e1e4e8" }}>
                                                                    <th style={{ padding: "10px", width: "90px" }}>ID</th>
                                                                    <th style={{ padding: "10px", width: "90px" }}>Severity</th>
                                                                    <th style={{ padding: "10px", width: "120px" }}>Category</th>
                                                                    <th style={{ padding: "10px", width: "70px" }}>Line</th>
                                                                    <th style={{ padding: "10px" }}>Finding & Action Item</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody>
                                                                {reviewReport.recommendations.map((rec) => {
                                                                    const isCritical = ["Critical", "High"].includes(rec?.severity);
                                                                    const isWarning = rec?.severity === "Medium";
                                                                    
                                                                    return (
                                                                        <tr key={rec?.id} style={{ borderBottom: "1px solid #e1e4e8", verticalAlign: "top" }}>
                                                                            <td style={{ padding: "10px", fontWeight: "bold", color: "#0366d6" }}><code>{rec?.id}</code></td>
                                                                            <td style={{ padding: "10px" }}>
                                                                                <span style={{
                                                                                    background: isCritical ? "#fcd8d8" : isWarning ? "#fff3cd" : "#dbf2e3",
                                                                                    color: isCritical ? "#9e1c1c" : isWarning ? "#856404" : "#1e5e2f",
                                                                                    padding: "2px 6px", borderRadius: "4px", fontSize: "11px", fontWeight: "bold"
                                                                                }}>
                                                                                    {rec?.severity || "Info"}
                                                                                </span>
                                                                            </td>
                                                                            <td style={{ padding: "10px", color: "#24292e" }}>{rec?.category}</td>
                                                                            <td style={{ padding: "10px", color: "#586069" }}><code>{rec?.line > 0 ? rec.line : "Global"}</code></td>
                                                                            <td style={{ padding: "10px" }}>
                                                                                <div style={{ fontWeight: "bold", color: "#24292e", marginBottom: "4px" }}>{rec?.title}</div>
                                                                                <div style={{ color: "#586069", fontSize: "12px", marginBottom: "6px" }}><em>Observation:</em> {rec?.finding}</div>
                                                                                <div style={{ color: "#24292e", fontSize: "12.5px", background: "#f8f9fa", padding: "6px 10px", borderRadius: "4px", borderLeft: "3px solid #28a745" }}>
                                                                                    <strong>Fix:</strong> {rec?.recommendation}
                                                                                </div>
                                                                            </td>
                                                                        </tr>
                                                                    );
                                                                })}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {!reviewLoading && !reviewReport && !reviewError && (
                                        <div className="info-message">
                                            Select a working Lambda code file asset from the repository to initialize analysis.
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                {selectedFile &&
                    activeTab === "diagram" && (
                        <PlaceholderTab
                            title="Flow Diagram"
                            message={
                                "Contact-flow visualization will be added in a later phase."
                            }
                        />
                    )}

                {selectedFile &&
                    activeTab === "chat" && (
                        <PlaceholderTab
                            title="Chat"
                            message={
                                "The Ollama assistant will be connected in Phase 2."
                            }
                        />
                    )}

            </div>
        </div>
    );
}


function EmptySelection() {
    return (
        <div className="empty-state">
            <div className="empty-state-icon">
                📂
            </div>

            <h2>Select a repository file</h2>

            <p>
                Choose a file from Repo Explorer to
                view its content and available analysis.
            </p>
        </div>
    );
}


function DashboardTab({
    selectedFile,
    content,
    loading,
    error,
    auditReport,
    auditLoading,
    reviewReport
}) {
    const lineCount =
        content.length > 0
            ? content.split(/\r?\n/).length
            : 0;

    const extension =
        selectedFile.includes(".")
            ? selectedFile
                .split(".")
                .pop()
                .toUpperCase()
            : "Unknown";

    const auditStatus =
        auditLoading
            ? "Audit running"
            : auditReport?.success === false
                ? "Audit failed"
                : auditReport?.audit_passed === true
                    ? "Passed"
                    : auditReport?.audit_passed === false
                        ? "Needs attention"
                        : "Not applicable";

    return (
        <section>
            <div className="content-heading">
                <div>
                    <h2>Dashboard</h2>

                    <div className="selected-path">
                        {selectedFile}
                    </div>
                </div>

                <span className="file-type-badge">
                    {extension}
                </span>
            </div>

            <div className="summary-grid">
                <SummaryCard
                    label="File type"
                    value={extension}
                />

                <SummaryCard
                    label="Lines"
                    value={
                        loading
                            ? "Loading..."
                            : lineCount
                    }
                />

                <SummaryCard
                    label="Characters"
                    value={
                        loading
                            ? "Loading..."
                            : content.length
                                .toLocaleString()
                    }
                />

                <SummaryCard
                    label="Flow audit"
                    value={auditStatus}
                />
                {isLambdaFile(selectedFile) && (
                    <>
                        <SummaryCard
                            label="Risk Level"
                            value={
                                reviewReport?.overallRisk ??
                                "Not Reviewed"
                            }
                        />

                        <SummaryCard
                            label="Findings"
                            value={
                                reviewReport?.recommendations?.length ?? 0
                            }
                        />
                    </>
                )}
            </div>

            {isLambdaFile(selectedFile) &&
                        reviewReport?.summary && (
                <div className="executive-summary-card">
                    <h3>Executive Summary</h3>
                    <p>{reviewReport.summary}</p>
                </div>
            )}

            {error && (
                <ErrorMessage message={error} />
            )}

            {loading && (
                <LoadingMessage
                    message="Loading file content..."
                />
            )}

            {!loading && !error && (
                <div className="file-viewer-card">
                    <div className="viewer-header">
                        File Content
                    </div>

                    <pre className="file-content">
                        {content}
                    </pre>
                </div>
            )}
        </section>
    );
}


function FlowAuditTab({
    selectedFile,
    report,
    loading,
    error,
    lastAuditedAt,
    onRefresh
}) {
    const supported =
        isContactFlowFile(selectedFile);

    if (!supported) {
        return (
            <section>
                <div className="content-heading">
                    <div>
                        <h2>Flow Analysis</h2>

                        <div className="selected-path">
                            {selectedFile}
                        </div>
                    </div>
                </div>

                <div className="info-message">
                    Flow Analysis is available for JSON
                    files under the contact-flows folder.
                </div>
            </section>
        );
    }

    const metrics =
        report?.metrics || {};

    const complexityStatus =
        report?.status?.complexity;

    const flowSizeStatus =
        report?.status?.flow_size;

    return (
        <section>
            <div className="content-heading">
                <div>
                    <h2>Flow Analysis</h2>

                    <div className="selected-path">
                        {selectedFile}
                    </div>
                </div>

                <button
                    type="button"
                    className="refresh-button"
                    onClick={onRefresh}
                    disabled={loading}
                >
                    <span
                        className={
                            loading
                                ? "refresh-icon spinning"
                                : "refresh-icon"
                        }
                    >
                        ↻
                    </span>

                    {loading
                        ? "Running Audit..."
                        : "Refresh Audit"}
                </button>
            </div>

            {lastAuditedAt && !loading && (
                <div className="audit-timestamp">
                    Last audited:{" "}
                    {lastAuditedAt.toLocaleString()}
                </div>
            )}

            {loading && (
                <LoadingMessage
                    message="Auditing the selected contact flow..."
                />
            )}

            {error && (
                <ErrorMessage message={error} />
            )}

            {!loading &&
                !error &&
                report?.success === false && (
                    <ErrorMessage
                        message={
                            report.message ||
                            "The flow audit failed."
                        }
                    />
                )}

            {!loading &&
                !error &&
                report?.success !== false &&
                report && (
                    <>
                        <div className="audit-status-row">
                            <StatusBadge
                                passed={
                                    report.audit_passed
                                }
                            />

                            {complexityStatus && (
                                <AssessmentBadge
                                    status={
                                        complexityStatus
                                    }
                                />
                            )}

                            {flowSizeStatus && (
                                <AssessmentBadge
                                    status={
                                        flowSizeStatus
                                    }
                                />
                            )}
                        </div>

                        <div className="metrics-grid">
                            <MetricCard
                                label="Total Blocks"
                                value={
                                    metrics.total_blocks
                                }
                            />

                            <MetricCard
                                label="Total Edges"
                                value={
                                    metrics.total_edges
                                }
                            />

                            <MetricCard
                                label="McCabe Complexity"
                                value={
                                    metrics
                                        .cyclomatic_complexity_mccabe
                                }
                            />

                            <MetricCard
                                label="Decision Complexity"
                                value={
                                    metrics
                                        .cyclomatic_complexity_decision
                                }
                            />

                            <MetricCard
                                label="Lambda Integrations"
                                value={
                                    metrics
                                        .lambda_integrations
                                }
                            />

                            <MetricCard
                                label="Unhandled Errors"
                                value={
                                    metrics
                                        .unhandled_error_blocks
                                }
                                warning={
                                    metrics
                                        .unhandled_error_blocks > 0
                                }
                            />
                        </div>

                        <div className="report-section">
                            <h3>Recommendations</h3>

                            <RecommendationList
                                recommendations={
                                    report.recommendations
                                }
                            />
                        </div>

                        {Array.isArray(
                            metrics.lambda_action_ids
                        ) &&
                            metrics
                                .lambda_action_ids
                                .length > 0 && (
                                <div className="report-section">
                                    <h3>
                                        Lambda Action IDs
                                    </h3>

                                    <ul className="detail-list">
                                        {metrics
                                            .lambda_action_ids
                                            .map((id) => (
                                                <li key={id}>
                                                    <code>
                                                        {id}
                                                    </code>
                                                </li>
                                            ))}
                                    </ul>
                                </div>
                            )}

                        {Array.isArray(
                            metrics
                                .unhandled_error_action_ids
                        ) &&
                            metrics
                                .unhandled_error_action_ids
                                .length > 0 && (
                                <div className="report-section warning-section">
                                    <h3>
                                        Actions Requiring
                                        Error Handling
                                    </h3>

                                    <ul className="detail-list">
                                        {metrics
                                            .unhandled_error_action_ids
                                            .map((id) => (
                                                <li key={id}>
                                                    <code>
                                                        {id}
                                                    </code>
                                                </li>
                                            ))}
                                    </ul>
                                </div>
                            )}
                    </>
                )}

            {!loading &&
                !error &&
                !report && (
                    <div className="info-message">
                        No audit report is currently
                        available. Select Refresh Audit to
                        run the analysis.
                    </div>
                )}
        </section>
    );
}


function SummaryCard({
    label,
    value
}) {
    return (
        <div className="summary-card">
            <div className="summary-label">
                {label}
            </div>

            <div className="summary-value">
                {value ?? "N/A"}
            </div>
        </div>
    );
}


function MetricCard({
    label,
    value,
    warning = false
}) {
    return (
        <div
            className={
                warning
                    ? "metric-card metric-warning"
                    : "metric-card"
            }
        >
            <div className="metric-label">
                {label}
            </div>

            <div className="metric-value">
                {value ?? 0}
            </div>
        </div>
    );
}


function StatusBadge({
    passed
}) {
    return (
        <span
            className={
                passed
                    ? "status-badge status-pass"
                    : "status-badge status-fail"
            }
        >
            {passed
                ? "✓ Audit Passed"
                : "⚠ Needs Attention"}
        </span>
    );
}


function AssessmentBadge({
    status
}) {
    const level =
        status?.level || "unknown";

    return (
        <span
            className={
                `assessment-badge assessment-${level}`
            }
            title={status?.message || ""}
        >
            {status?.label || level}
        </span>
    );
}


function RecommendationList({
    recommendations
}) {
    if (
        !Array.isArray(recommendations) ||
        recommendations.length === 0
    ) {
        return (
            <p>No recommendations were returned.</p>
        );
    }

    return (
        <ul className="recommendation-list">
            {recommendations.map(
                (recommendation, index) => (
                    <li
                        key={`${index}-${recommendation}`}
                    >
                        {recommendation}
                    </li>
                )
            )}
        </ul>
    );
}


function LoadingMessage({
    message
}) {
    return (
        <div className="loading-message">
            <span className="loading-spinner" />
            {message}
        </div>
    );
}


function ErrorMessage({
    message
}) {
    return (
        <div
            className="error-message"
            role="alert"
        >
            <strong>Unable to complete the request.</strong>
            <span>{message}</span>
        </div>
    );
}


function PlaceholderTab({
    title,
    message
}) {
    return (
        <section>
            <h2>{title}</h2>

            <div className="info-message">
                {message}
            </div>
        </section>
    );
}



