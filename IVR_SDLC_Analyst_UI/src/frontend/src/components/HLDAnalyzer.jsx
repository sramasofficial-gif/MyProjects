import React, { useEffect, useMemo, useRef, useState } from "react";
import {
    generateHLDMatrix,
    clearHLDMatrixCache,
} from "../services/api";

const TYPE_LABELS = {
    table: "Table",
    image: "Image",
    diagram: "Diagram",
    "diagram-iframe": "Diagram (iframe)",
    text: "Text",
    "unresolved-macro": "Unresolved macro",
};

const REPORT = {
    ink: "#16212e",
    inkSoft: "#4a5a6b",
    line: "#d9e0e7",
    panel: "#ffffff",
    bg: "#eef1f4",
    accent: "#2a5b8c",
    accentSoft: "#e4edf6",
    ok: "#2f7d4f",
    okBg: "#e5f3ea",
    issue: "#b4570a",
    issueBg: "#fbead9",
    empty: "#8a94a0",
    emptyBg: "#eef0f2",
    muted: "#f1f3f5",
    purpleBg: "#efe6f7",
    purple: "#6b3fa0",
    greenBg: "#e7f4ee",
    green: "#227a52",
    yellowBg: "#fdf3d8",
    yellow: "#96700a",
    mono: "SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace",
    sans: "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
};

const REVIEW_SCOPE_OPTIONS = [
    { id: "functional", label: "Functional Completeness", description: "Requirements, business rules and workflows" },
    { id: "architecture", label: "Architecture", description: "Components, topology, design and data flow" },
    { id: "security", label: "Security", description: "Authentication, authorization, IAM and data protection" },
    { id: "vulnerability", label: "Vulnerability", description: "Threats, attack surface and exploitable weaknesses" },
    { id: "performance", label: "Performance", description: "Latency, throughput, capacity and scalability" },
    { id: "reliability", label: "Reliability & Availability", description: "Failover, recovery, retries and resilience" },
    { id: "integration", label: "Integration", description: "APIs, events, Lambda and external interfaces" },
    { id: "compliance", label: "Compliance", description: "Policies, retention and regulatory controls" },
    { id: "documentation", label: "Documentation Quality", description: "Completeness, clarity and terminology" },
    { id: "testability", label: "Testability", description: "Validation, QA, automation and test coverage" },
    { id: "cost", label: "Cost Optimization", description: "Sizing, consumption, licensing and cost" },
    { id: "ivr", label: "IVR / Contact Center", description: "Amazon Connect, IVR, queues, prompts and flows" },
];

const DEFAULT_REVIEW_SCOPES = ["architecture", "security", "integration", "ivr"];

// FastAPI backend base URL. The Vite dev server is running on :5173,
// while the HLD APIs are served by Uvicorn on :8000.
const BACKEND_API_BASE = "http://127.0.0.1:8000";

function typeLabel(type = "") {
    return TYPE_LABELS[type] || (String(type).startsWith("macro:") ? String(type).slice(6) : type);
}

function typeBadgeStyle(type) {
    if (type === "table") return { background: REPORT.accentSoft, color: REPORT.accent };
    if (type === "diagram" || type === "diagram-iframe") return { background: REPORT.purpleBg, color: REPORT.purple };
    if (type === "image") return { background: REPORT.greenBg, color: REPORT.green };
    if (type === "unresolved-macro") return { background: REPORT.issueBg, color: REPORT.issue };
    if (String(type).startsWith("macro:")) return { background: REPORT.yellowBg, color: REPORT.yellow };
    return { background: REPORT.emptyBg, color: REPORT.inkSoft };
}

function statusPill(status) {
    const map = {
        ok: ["status-ok", "OK", REPORT.okBg, REPORT.ok],
        issue: ["status-issue", "Check", REPORT.issueBg, REPORT.issue],
        empty: ["status-empty", "Empty", REPORT.emptyBg, REPORT.empty],
    };
    const [cls, label, background, color] = map[status] || map.empty;
    return (
        <span
            className={`status-pill ${cls}`}
            style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 5,
                fontSize: 11.5,
                fontWeight: 600,
                padding: "3px 9px",
                borderRadius: 100,
                background,
                color,
                whiteSpace: "nowrap",
            }}
        >
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "currentColor" }} />
            {label}
        </span>
    );
}

function extractNumbering(title = "") {
    const match = String(title).trim().match(/^([0-9]+(?:\.[0-9]+)*)\b/);
    return match ? match[1] : "—";
}

export default function HLDAnalyzer() {
    const [wikiURL, setWikiURL] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [verificationMatrix, setVerificationMatrix] = useState(null);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [isLoadedFromCache, setIsLoadedFromCache] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [typeFilter, setTypeFilter] = useState("");
    const [statusFilter, setStatusFilter] = useState("");
    const [selectedIds, setSelectedIds] = useState(new Set());
    const [expandedId, setExpandedId] = useState(null);
    const [selectedReviewScopes, setSelectedReviewScopes] = useState(DEFAULT_REVIEW_SCOPES);
    const [reviewPlan, setReviewPlan] = useState(null);
    const [activeTab, setActiveTab] = useState("inventory");
    const [exportingExcel, setExportingExcel] = useState(false);
    const [excelExportError, setExcelExportError] = useState("");
    const [reviewJob, setReviewJob] = useState(null);
    const [reviewJobId, setReviewJobId] = useState(null);
    const reviewPollRef = useRef(null);
    const restoringStateRef = useRef(true);

    useEffect(() => {
        let cancelled = false;

        async function restorePageState() {
            const savedUrl = localStorage.getItem("hld.lastDocumentUrl") || "";
            const savedScopes = localStorage.getItem("hld.selectedScopes");
            const savedIds = localStorage.getItem("hld.selectedSectionIds");

            let restoredScopes = DEFAULT_REVIEW_SCOPES;
            let restoredIds = [];

            if (savedScopes) {
                try {
                    const parsed = JSON.parse(savedScopes);
                    if (Array.isArray(parsed) && parsed.length) {
                        restoredScopes = parsed;
                        if (!cancelled) setSelectedReviewScopes(parsed);
                    }
                } catch {}
            }

            if (savedIds) {
                try {
                    const parsed = JSON.parse(savedIds);
                    if (Array.isArray(parsed)) {
                        restoredIds = parsed.map(Number).filter(Number.isFinite);
                        if (!cancelled) setSelectedIds(new Set(restoredIds));
                    }
                } catch {}
            }

            if (savedUrl) {
                if (!cancelled) setWikiURL(savedUrl);

                try {
                    const matrixData = await generateHLDMatrix(savedUrl);

                    if (cancelled) return;

                    setVerificationMatrix(
                        Array.isArray(matrixData.matrix)
                            ? matrixData.matrix
                            : []
                    );
                    setIsLoadedFromCache(
                        Boolean(matrixData.loaded_from_cache)
                    );

                    // Recover a backend-owned review independently of the old
                    // localStorage job ID. This is the key refresh-recovery path.
                    const activeJob = await discoverActiveReviewJob(
                        savedUrl,
                        restoredScopes,
                        restoredIds,
                    );

                    if (cancelled) return;

                    if (activeJob?.job_id) {
                        console.info(
                            "[HLD REVIEW] Backend review job restored:",
                            activeJob.job_id,
                            activeJob.status
                        );
                        setReviewJob(activeJob);
                        persistJobId(activeJob.job_id);

                        if (
                            activeJob.status === "COMPLETED" &&
                            activeJob.result?.segmented_blueprint
                        ) {
                            setAnalysisResult(activeJob.result.segmented_blueprint);
                            setActiveTab("findings");
                        } else {
                            setActiveTab("review");
                        }
                    } else {
                        // Do not keep a stale localStorage ID alive when the
                        // backend confirms that no matching job exists.
                        clearStoredReviewJob();
                        setReviewJobId(null);
                        setReviewJob(null);
                        setAnalysisResult(null);
                    }
                } catch (err) {
                    if (cancelled) return;
                    console.warn(
                        "[HLD REVIEW] Initial page-state recovery failed:",
                        err
                    );
                }
            }

            if (!cancelled) {
                restoringStateRef.current = false;
            }
        }

        restorePageState();

        return () => {
            cancelled = true;
        };
    }, []);

    useEffect(() => {
        if (restoringStateRef.current) return;
        if (!wikiURL.trim()) return;
        localStorage.setItem("hld.lastDocumentUrl", wikiURL.trim());
        localStorage.setItem("hld.selectedScopes", JSON.stringify(selectedReviewScopes));
        localStorage.setItem("hld.selectedSectionIds", JSON.stringify(Array.from(selectedIds)));
    }, [wikiURL, selectedReviewScopes, selectedIds]);

    function persistJobId(jobId) {
        setReviewJobId(jobId || null);
        if (jobId) localStorage.setItem("hld.activeReviewJobId", jobId);
        else localStorage.removeItem("hld.activeReviewJobId");
    }

    async function getHLDJson(path) {
        const url = path.startsWith("http")
            ? path
            : `${BACKEND_API_BASE}${path}`;

        const response = await fetch(url);
        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            const err = new Error(
                data.detail ||
                data.message ||
                `Request failed (${response.status}) for ${url}`
            );
            err.status = response.status;
            err.code = data.code || null;
            throw err;
        }

        return data;
    }

    async function discoverActiveReviewJob(documentUrl, scopes, sectionIds) {
        if (!documentUrl?.trim()) return null;

        const params = new URLSearchParams();
        params.set("document_url", documentUrl.trim());

        if (Array.isArray(scopes) && scopes.length) {
            params.set("review_scopes", scopes.join(","));
        }

        if (Array.isArray(sectionIds) && sectionIds.length) {
            params.set(
                "selected_section_ids",
                sectionIds.map(Number).filter(Number.isFinite).join(",")
            );
        }

        const data = await getHLDJson(
            `/api/hld/review/active?${params.toString()}`
        );

        return data.found ? data.job : null;
    }

    function clearStoredReviewJob(jobId = null) {
        const storedJobId = localStorage.getItem(
            "hld.activeReviewJobId"
        );

        if (!jobId || storedJobId === jobId) {
            localStorage.removeItem(
                "hld.activeReviewJobId"
            );
        }
    }

    async function refreshReviewJob(jobId) {
        if (!jobId) return null;

        try {
            const data = await getHLDJson(
                `/api/hld/review/${encodeURIComponent(jobId)}`
            );

            const job = data.job;

            if (!job) {
                throw new Error("Review job was not returned by the backend.");
            }

            setReviewJob(job);

            return job;

        } catch (err) {
            // A missing job is a stale browser reference, not a transient error.
            if (err?.status === 404 || /404|not found/i.test(err?.message || "")) {
                console.warn(
                    `[HLD REVIEW] Stale job ID removed: ${jobId}`
                );

                clearStoredReviewJob(jobId);

                setReviewJob(null);
                setReviewJobId(null);
                setActiveTab("inventory");

                return null;
            }

            throw err;
        }
    }

    useEffect(() => {
        if (!reviewJobId) {
            return undefined;
        }

        let cancelled = false;

        const poll = async () => {
            if (cancelled) return;

            try {
                const job = await refreshReviewJob(reviewJobId);

                if (cancelled) return;

                if (!job) {
                    // Stale/missing job. refreshReviewJob() already cleaned it.
                    return;
                }

                if (
                    ["QUEUED", "RUNNING", "CANCEL_REQUESTED"]
                        .includes(job.status)
                ) {
                    reviewPollRef.current = window.setTimeout(
                        poll,
                        1500
                    );
                }

            } catch (err) {
                if (cancelled) return;

                console.error(
                    "[HLD REVIEW] Poll failed:",
                    err
                );

                // Transient network/server problem:
                // keep polling.
                reviewPollRef.current = window.setTimeout(
                    poll,
                    3000
                );
            }
        };

        poll();

        return () => {
            cancelled = true;

            if (reviewPollRef.current) {
                window.clearTimeout(
                    reviewPollRef.current
                );

                reviewPollRef.current = null;
            }
        };
    }, [reviewJobId]);

    useEffect(() => {
        return () => {
            if (reviewPollRef.current) window.clearTimeout(reviewPollRef.current);
        };
    }, []);

    function handleURLChange(e) {
        setWikiURL(e.target.value);
        setError("");
        setVerificationMatrix(null);
        setAnalysisResult(null);
        setIsLoadedFromCache(false);
        setSearchQuery("");
        setTypeFilter("");
        setStatusFilter("");
        setSelectedIds(new Set());
        setExpandedId(null);
        setReviewPlan(null);
        setActiveTab("inventory");
        setReviewJob(null);
        persistJobId(null);
    }

    async function triggerPhase1MatrixIngestion() {
        if (!wikiURL.trim()) return;

        setLoading(true);
        setError("");
        setVerificationMatrix(null);
        setAnalysisResult(null);
        setSelectedIds(new Set());
        setExpandedId(null);
        setReviewPlan(null);
        setActiveTab("inventory");

        try {
            const data = await generateHLDMatrix(wikiURL.trim());
            setVerificationMatrix(Array.isArray(data.matrix) ? data.matrix : []);
            setIsLoadedFromCache(Boolean(data.loaded_from_cache));
        } catch (err) {
            setError(err.message || "Failed to process wiki document matrix.");
        } finally {
            setLoading(false);
        }
    }

    async function invalidateCurrentReviewJob() {
        const jobId = reviewJobId;
        const activeStatuses = ["QUEUED", "RUNNING", "CANCEL_REQUESTED"];

        if (reviewPollRef.current) {
            window.clearTimeout(reviewPollRef.current);
            reviewPollRef.current = null;
        }

        try {
            if (jobId) {
                const activeJob = reviewJob;

                if (activeJob && activeStatuses.includes(activeJob.status)) {
                    await postHLDJson(
                        `/api/hld/review/${encodeURIComponent(jobId)}/cancel`,
                        {}
                    );
                }
            }
        } catch (err) {
            console.warn(
                "[HLD REVIEW] Unable to cancel previous review before re-scrape:",
                err
            );
        } finally {
            clearStoredReviewJob(jobId);
            setReviewJobId(null);
            setReviewJob(null);
            setAnalysisResult(null);
        }
    }

    /*
    async function handleForcedCacheClear() {
        const targetUrl = wikiURL.trim();
        if (!targetUrl) return;

        // Preserve the URL as the source-of-truth for the entire refresh operation.
        // Do not depend on React state updates while clearing/rebuilding the matrix.
        setLoading(true);
        setError("");
        setWikiURL(targetUrl);
        setVerificationMatrix(null);
        setAnalysisResult(null);
        setIsLoadedFromCache(false);
        setSelectedIds(new Set());
        setExpandedId(null);
        setReviewPlan(null);
        setActiveTab("inventory");

        try {
            await clearHLDMatrixCache(targetUrl);

            // Re-ingest directly with the preserved URL rather than calling
            // triggerPhase1MatrixIngestion(), which reads the asynchronously
            // updated wikiURL React state.
            const data = await generateHLDMatrix(targetUrl);
            setWikiURL(targetUrl);
            setVerificationMatrix(Array.isArray(data.matrix) ? data.matrix : []);
            setIsLoadedFromCache(Boolean(data.loaded_from_cache));
        } catch (err) {
            // Keep the URL visible even when the re-scrape fails so the user
            // knows exactly which document was being refreshed.
            setWikiURL(targetUrl);
            setError(err.message || "Failed to refresh the Confluence HLD matrix.");
        } finally {
            setLoading(false);
        }
    }
    */

    async function handleForcedCacheClear() {
        const targetUrl = wikiURL.trim();
        if (!targetUrl) return;

        await invalidateCurrentReviewJob();

        setLoading(true);
        setError("");
        setVerificationMatrix(null);

        try {
            await clearHLDMatrixCache(targetUrl);
            const data = await generateHLDMatrix(targetUrl);

            setWikiURL(targetUrl);
            setVerificationMatrix(
                Array.isArray(data.matrix) ? data.matrix : []
            );
            setIsLoadedFromCache(Boolean(data.loaded_from_cache));
            setActiveTab("inventory");
        } catch (err) {
            setWikiURL(targetUrl);
            setError(
                err.message || "Failed to refresh the HLD matrix."
            );
        } finally {
            setLoading(false);
        }
    }

    function toggleReviewScope(scopeId) {
        setSelectedReviewScopes((previous) => {
            const next = new Set(previous);
            if (next.has(scopeId)) next.delete(scopeId);
            else next.add(scopeId);
            return Array.from(next);
        });
        setReviewPlan(null);
        setActiveTab("inventory");
    }

    async function postHLDJson(path, body) {
        const url = path.startsWith("http") ? path : `${BACKEND_API_BASE}${path}`;
        console.log("[HLD API] POST", url);
        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            const err = new Error(
                data.detail ||
                data.message ||
                `Request failed (${response.status}) for ${url}`
            );
            err.status = response.status;
            err.code = data.code || null;
            throw err;
        }
        return data;
    }

    async function buildReviewPlan() {
        if (!wikiURL.trim()) return;
        if (selectedReviewScopes.length === 0) {
            setError("Select at least one review scope before building the review plan.");
            return;
        }

        setLoading(true);
        setError("");
        setReviewPlan(null);
        try {
            const data = await postHLDJson("/api/hld/review-plan", {
                document_title: wikiURL.trim(),
                review_scopes: selectedReviewScopes,
                selected_section_ids: Array.from(selectedIds),
            });
            setReviewPlan(data);
            setActiveTab("plan");
            return data;
        } catch (err) {
            setError(err.message || "Failed to build the HLD review plan.");
        } finally {
            setLoading(false);
        }
    }

    async function confirmAndTriggerLLMReview() {
        if (!wikiURL.trim()) return;
        if (selectedReviewScopes.length === 0) {
            setError("Select at least one review scope before starting the AI review.");
            return;
        }
        if (!verificationMatrix) {
            setError("Build the HLD section inventory before starting the AI review.");
            return;
        }

        setLoading(true);
        setError("");
        setActiveTab("review");

        try {
            const plan = await postHLDJson("/api/hld/review-plan", {
                document_title: wikiURL.trim(),
                review_scopes: selectedReviewScopes,
                selected_section_ids: Array.from(selectedIds),
            });
            setReviewPlan(plan);

            if (!plan.eligible_section_ids?.length) {
                throw new Error("The current review scope and section selection produced no reviewable HLD sections.");
            }

            const response = await postHLDJson("/api/hld/review/start", {
                document_title: wikiURL.trim(),
                project_scope: "IVR Context Validation",
                review_scopes: selectedReviewScopes,
                selected_section_ids: plan.eligible_section_ids,
            });

            const job = response.job;
            if (!job?.job_id) throw new Error("The backend did not return a review job ID.");
            setReviewJob(job);
            persistJobId(job.job_id);
            setActiveTab("review");
        } catch (err) {
            setError(err.message || "Failed to start the scoped architectural audit.");
        } finally {
            setLoading(false);
        }
    }

    async function cancelActiveReview() {
        if (!reviewJobId) return;
        try {
            const data = await postHLDJson(`/api/hld/review/${encodeURIComponent(reviewJobId)}/cancel`, {});
            setReviewJob(data.job);
            setActiveTab("review");
        } catch (err) {
            setError(err.message || "Failed to request review cancellation.");
        }
    }

    const matrixRows = useMemo(() => {
        const rows = Array.isArray(verificationMatrix) ? verificationMatrix : [];
        const q = searchQuery.trim().toLowerCase();

        return rows
            .map((chunk, index) => {
                const metadata = chunk?.metadata || {};
                const types = Array.isArray(metadata.types) ? metadata.types : (Array.isArray(chunk?.types) ? chunk.types : []);
                const status = metadata.status || chunk?.status || (metadata.placeholderCount ? "issue" : (types.length ? "ok" : "empty"));
                const level = Number(metadata.level || chunk?.level || 1);
                const heading = metadata.parent_section || chunk?.heading || "Unclassified section";
                return {
                    ...chunk,
                    id: Number(chunk?.id || index + 1),
                    parentSection: heading,
                    numbering: metadata.numbering || chunk?.numbering || extractNumbering(heading),
                    level,
                    types,
                    status,
                    placeholderCount: Number(metadata.placeholderCount || chunk?.placeholderCount || 0),
                    auditTags: Array.isArray(metadata.audit_tags) ? metadata.audit_tags : (Array.isArray(chunk?.audit_tags) ? chunk.audit_tags : []),
                    visualEvidence: Array.isArray(chunk?.visual_evidence)
                        ? chunk.visual_evidence
                        : (Array.isArray(metadata.visual_evidence) ? metadata.visual_evidence : []),
                    visualReviewAvailable: Boolean(chunk?.visual_review_available || metadata.visual_review_available),
                    visualReviewAnalyzed: Boolean(chunk?.visual_review_analyzed || metadata.visual_review_analyzed),
                    wordCount: String(chunk?.content || "").trim()
                        ? String(chunk.content).trim().split(/\s+/).length
                        : 0,
                };
            })
            .filter((row) => {
                if (q && !row.parentSection.toLowerCase().includes(q)) return false;
                if (typeFilter && !row.types.includes(typeFilter)) return false;
                if (statusFilter && row.status !== statusFilter) return false;
                return true;
            });
    }, [verificationMatrix, searchQuery, typeFilter, statusFilter]);

    const stats = useMemo(() => {
        const rows = Array.isArray(verificationMatrix) ? verificationMatrix : [];
        const withTables = rows.filter((r) => (r?.metadata?.types || r?.types || []).includes("table")).length;
        const withDiagrams = rows.filter((r) => {
            const types = r?.metadata?.types || r?.types || [];
            return types.includes("diagram") || types.includes("diagram-iframe");
        }).length;
        const issues = rows.filter((r) => {
            const types = r?.metadata?.types || r?.types || [];
            const status = r?.metadata?.status || r?.status || (r?.metadata?.placeholderCount ? "issue" : (types.length ? "ok" : "empty"));
            return status === "issue";
        }).length;
        const withVisualEvidence = rows.filter((r) => {
            const evidence = r?.visual_evidence || r?.metadata?.visual_evidence || [];
            return Array.isArray(evidence) && evidence.length > 0;
        }).length;
        return {
            total: rows.length,
            withTables,
            withDiagrams,
            withVisualEvidence,
            issues,
        };
    }, [verificationMatrix]);

    const allVisibleSelected =
        matrixRows.length > 0 && matrixRows.every((row) => selectedIds.has(row.id));

    function toggleRow(id) {
        setSelectedIds((previous) => {
            const next = new Set(previous);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
        setReviewPlan(null);
    }

    function toggleSelectAllVisible() {
        setSelectedIds((previous) => {
            const next = new Set(previous);
            if (allVisibleSelected) {
                matrixRows.forEach((row) => next.delete(row.id));
            } else {
                matrixRows.forEach((row) => next.add(row.id));
            }
            return next;
        });
        setReviewPlan(null);
    }

    async function copySelectedHeadings() {
        const sourceRows = Array.isArray(verificationMatrix) ? verificationMatrix : [];
        const chosen = sourceRows
            .map((chunk, index) => ({
                id: index + 1,
                heading: chunk?.metadata?.parent_section || "Unclassified section",
            }))
            .filter((row) => selectedIds.has(row.id));

        const text = chosen
            .map((row) => `${extractNumbering(row.heading) !== "—" ? `${extractNumbering(row.heading)} ` : ""}${row.heading}`)
            .join("\n");

        if (!text) return;

        try {
            await navigator.clipboard.writeText(text);
        } catch (err) {
            setError("Unable to copy selected headings to the clipboard.");
        }
    }

    async function downloadExcelReport() {
        if (!analysisResult || !wikiURL) return;
        setExportingExcel(true);
        setExcelExportError("");
        try {
            const response = await fetch(`${BACKEND_API_BASE}/api/hld/export-excel`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    document_title: wikiURL,
                    review_result: analysisResult,
                    selected_section_ids: Array.from(selectedIds),
                }),
            });
            if (!response.ok) throw new Error(await response.text() || "Failed to generate Excel report.");
            const blob = await response.blob();
            const disposition = response.headers.get("content-disposition") || "";
            const match = disposition.match(/filename="?([^";]+)"?/i);
            const filename = match?.[1] || "HLD_Review.xlsx";
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url; a.download = filename;
            document.body.appendChild(a); a.click(); a.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            setExcelExportError(err.message || "Failed to generate Excel report.");
        } finally {
            setExportingExcel(false);
        }
    }

    function resetFilters() {
        setSearchQuery("");
        setTypeFilter("");
        setStatusFilter("");
    }

    const showReport = Boolean(verificationMatrix && !analysisResult && !loading && activeTab === "inventory");

    return (
        <section
            className="hld-analyzer-panel"
            style={{
                padding: 20,
                fontFamily: REPORT.sans,
                display: "grid",
                gridTemplateColumns: "300px minmax(0, 1fr)",
                gridTemplateRows: "minmax(0, 1fr)",
                gap: 18,
                background: REPORT.bg,
                height: "calc(100vh - 80px)",
                minHeight: 0,
                overflow: "hidden",
                boxSizing: "border-box",
                color: REPORT.ink,
            }}
        >
            {/* Control panel */}
            <aside
                style={{
                    background: REPORT.panel,
                    border: `1px solid ${REPORT.line}`,
                    borderRadius: 8,
                    padding: 18,
                    height: "100%",
                    minHeight: 0,
                    overflowY: "auto",
                    overflowX: "hidden",
                    alignSelf: "stretch",
                    position: "relative",
                    boxSizing: "border-box",
                }}
            >
                <div style={{ marginBottom: 18 }}>
                    <h3
                        style={{
                            margin: 0,
                            color: REPORT.ink,
                            fontSize: 18,
                            fontWeight: 650,
                        }}
                    >
                        Confluence HLD Portal
                    </h3>
                    <p
                        style={{
                            margin: "4px 0 0",
                            color: REPORT.inkSoft,
                            fontSize: 12,
                        }}
                    >
                        Live wiki parsing and architectural review workspace.
                    </p>
                </div>

                <div
                    style={{
                        background: "#f6f8fa",
                        border: `1px dashed ${REPORT.line}`,
                        borderRadius: 6,
                        padding: 12,
                        marginBottom: 12,
                    }}
                >
                    <label
                        style={{
                            display: "block",
                            marginBottom: 7,
                            fontWeight: 650,
                            fontSize: 12,
                            color: REPORT.ink,
                        }}
                    >
                        Atlassian Wiki Page URL
                    </label>
                    <input
                        type="text"
                        placeholder="https://reqcentral.com/wiki/spaces/..."
                        value={wikiURL}
                        onChange={handleURLChange}
                        disabled={
                            loading ||
                            Boolean(
                                reviewJob &&
                                ["QUEUED", "RUNNING", "CANCEL_REQUESTED"].includes(reviewJob.status)
                            )
                        }
                        aria-label="Atlassian Wiki Page URL"
                        style={{
                            width: "100%",
                            padding: "8px 9px",
                            border: `1px solid ${REPORT.line}`,
                            borderRadius: 6,
                            fontSize: 12,
                            fontFamily: REPORT.mono,
                            outline: "none",
                            background: loading ? REPORT.muted : REPORT.panel,
                            color: REPORT.ink,
                            opacity: 1,
                        }}
                    />
                </div>

                {!verificationMatrix ? (
                    <button
                        onClick={triggerPhase1MatrixIngestion}
                        disabled={loading || !wikiURL.trim()}
                        style={{
                            width: "100%",
                            background: REPORT.accent,
                            color: "#fff",
                            padding: "10px 12px",
                            border: "none",
                            borderRadius: 6,
                            fontWeight: 650,
                            cursor: loading || !wikiURL.trim() ? "not-allowed" : "pointer",
                            opacity: loading || !wikiURL.trim() ? 0.6 : 1,
                        }}
                    >
                        {loading ? "Extracting Wiki Data..." : "Ingest & Build Matrix"}
                    </button>
                ) : (
                    <div
                        style={{
                            background: REPORT.issueBg,
                            padding: 12,
                            borderRadius: 6,
                            border: `1px solid #edc59f`,
                        }}
                    >
                        <div
                            style={{
                                color: REPORT.issue,
                                fontSize: 12,
                                fontWeight: 650,
                                marginBottom: 8,
                            }}
                        >
                            Matrix asset available
                        </div>
                        <button
                            onClick={handleForcedCacheClear}
                            disabled={loading}
                            style={{
                                width: "100%",
                                background: REPORT.issue,
                                color: "#fff",
                                padding: "8px 10px",
                                border: "none",
                                borderRadius: 5,
                                fontSize: 12,
                                fontWeight: 650,
                                cursor: loading ? "not-allowed" : "pointer",
                                opacity: loading ? 0.6 : 1,
                            }}
                        >
                            Re-Scrape Page Fresh
                        </button>
                    </div>
                )}

                {isLoadedFromCache && verificationMatrix && (
                    <div
                        style={{
                            marginTop: 10,
                            background: REPORT.accentSoft,
                            color: REPORT.accent,
                            padding: "7px 9px",
                            borderRadius: 6,
                            fontSize: 11.5,
                            fontWeight: 650,
                        }}
                    >
                        Loaded from disk cache
                    </div>
                )}

                {verificationMatrix && (
                    <div
                        style={{
                            marginTop: 14,
                            background: "#f6f8fa",
                            border: `1px solid ${REPORT.line}`,
                            borderRadius: 6,
                            padding: 12,
                        }}
                    >
                        <div style={{ fontSize: 12.5, fontWeight: 650, color: REPORT.ink, marginBottom: 4 }}>
                            Review Scope
                        </div>
                        <div style={{ fontSize: 11, color: REPORT.inkSoft, lineHeight: 1.4, marginBottom: 10 }}>
                            Choose the HLD review lenses. Only matching sections are sent to the AI review stage.
                        </div>

                        <div style={{ display: "grid", gap: 6, maxHeight: "none", overflow: "visible", paddingRight: 2 }}>
                            {REVIEW_SCOPE_OPTIONS.map((scope) => {
                                const checked = selectedReviewScopes.includes(scope.id);
                                return (
                                    <label
                                        key={scope.id}
                                        title={scope.description}
                                        style={{
                                            display: "flex",
                                            alignItems: "flex-start",
                                            gap: 8,
                                            padding: "7px 8px",
                                            background: checked ? REPORT.accentSoft : REPORT.panel,
                                            border: `1px solid ${checked ? "#b9cfe3" : REPORT.line}`,
                                            borderRadius: 5,
                                            cursor: "pointer",
                                        }}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={checked}
                                            onChange={() => toggleReviewScope(scope.id)}
                                            style={{ marginTop: 2 }}
                                        />
                                        <span>
                                            <span style={{ display: "block", fontSize: 11.5, fontWeight: 650, color: REPORT.ink }}>
                                                {scope.label}
                                            </span>
                                            <span style={{ display: "block", fontSize: 10.5, color: REPORT.inkSoft, marginTop: 1 }}>
                                                {scope.description}
                                            </span>
                                        </span>
                                    </label>
                                );
                            })}
                        </div>

                        <button
                            onClick={buildReviewPlan}
                            disabled={loading || selectedReviewScopes.length === 0}
                            style={{
                                width: "100%",
                                marginTop: 10,
                                background: REPORT.accent,
                                color: "#fff",
                                padding: "9px 10px",
                                border: "none",
                                borderRadius: 5,
                                fontSize: 12,
                                fontWeight: 650,
                                cursor: loading || selectedReviewScopes.length === 0 ? "not-allowed" : "pointer",
                                opacity: loading || selectedReviewScopes.length === 0 ? 0.6 : 1,
                            }}
                        >
                            {loading ? "Building Review Plan..." : "Build Review Plan"}
                        </button>
                    </div>
                )}

                {error && (
                    <div
                        style={{
                            marginTop: 12,
                            color: REPORT.issue,
                            background: REPORT.issueBg,
                            padding: 10,
                            borderRadius: 6,
                            border: `1px solid #edc59f`,
                            fontSize: 12,
                            lineHeight: 1.45,
                        }}
                    >
                        {error}
                    </div>
                )}
            </aside>

            {/* Report viewport */}
            <main style={{ minWidth: 0, minHeight: 0, height: "100%", overflow: "hidden", display: "flex", flexDirection: "column" }}>
                {verificationMatrix && (
                    <div
                        style={{
                            flex: "0 0 auto",
                            display: "flex",
                            gap: 4,
                            alignItems: "center",
                            padding: 4,
                            marginBottom: 10,
                            background: REPORT.panel,
                            border: `1px solid ${REPORT.line}`,
                            borderRadius: 8,
                        }}
                    >
                        {[
                            ["inventory", "Section Inventory"],
                            ["plan", "Review Plan"],
                            ["review", "AI Review"],
                            ["findings", "Findings"],
                            ["telemetry", "Telemetry"],
                        ].map(([id, label]) => (
                            <button
                                key={id}
                                onClick={() => setActiveTab(id)}
                                disabled={((id === "findings" || id === "telemetry") && !analysisResult) || (id === "review" && !verificationMatrix)}
                                style={{
                                    flex: 1,
                                    minWidth: 0,
                                    padding: "9px 10px",
                                    border: "none",
                                    borderRadius: 6,
                                    background: activeTab === id ? REPORT.accent : "transparent",
                                    color: activeTab === id ? "#fff" : REPORT.inkSoft,
                                    fontSize: 12.5,
                                    fontWeight: activeTab === id ? 700 : 600,
                                    cursor: (((id === "findings" || id === "telemetry") && !analysisResult) || (id === "review" && !verificationMatrix)) ? "not-allowed" : "pointer",
                                    opacity: ((id === "findings" || id === "telemetry") && !analysisResult) ? 0.45 : 1,
                                    whiteSpace: "nowrap",
                                }}
                            >
                                {label}
                            </button>
                        ))}
                    </div>
                )}
                {loading && (
                    <div
                        style={{
                            background: REPORT.panel,
                            border: `1px solid ${REPORT.line}`,
                            borderRadius: 8,
                            padding: "32px 24px",
                            textAlign: "center",
                            color: REPORT.inkSoft,
                        }}
                    >
                        <div
                            style={{
                                fontSize: 15,
                                fontWeight: 700,
                                color: REPORT.accent,
                                marginBottom: 8,
                            }}
                        >
                            Refreshing Confluence HLD
                        </div>

                        <div
                            style={{
                                fontSize: 12,
                                marginBottom: 8,
                            }}
                        >
                            Connecting to Atlassian Wiki Secure Node via Playwright execution layers...
                        </div>

                        <div
                            style={{
                                fontFamily: REPORT.mono,
                                fontSize: 11,
                                color: REPORT.inkSoft,
                                wordBreak: "break-all",
                            }}
                        >
                            {wikiURL}
                        </div>
                    </div>
                )}

                {!verificationMatrix && !loading && (
                    <div
                        style={{
                            background: REPORT.panel,
                            border: `2px dashed ${REPORT.line}`,
                            borderRadius: 8,
                            padding: "72px 30px",
                            textAlign: "center",
                            color: REPORT.inkSoft,
                        }}
                    >
                        <div style={{ fontSize: 20, fontWeight: 650, color: REPORT.ink, marginBottom: 6 }}>
                            HLD Section Inventory
                        </div>
                        <div style={{ fontSize: 13 }}>
                            Enter a valid Confluence specification URL to initialize the validation matrix.
                        </div>
                    </div>
                )}


                {activeTab === "plan" && verificationMatrix && !loading && (
                    <div style={{ flex: 1, minHeight: 0, overflowY: "auto", overflowX: "hidden", paddingRight: 4, paddingBottom: 16, }}>
{reviewPlan && (
    <div
        style={{
            background: REPORT.panel,
            border: `1px solid ${REPORT.line}`,
            borderRadius: 8,
            padding: "12px 14px",
            marginBottom: 14,
        }}
    >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
            <div>
                <div style={{ fontSize: 13, fontWeight: 650, color: REPORT.ink }}>
                    Review Plan
                </div>
                <div style={{ fontSize: 11.5, color: REPORT.inkSoft, marginTop: 3 }}>
                    {selectedIds.size > 0
                        ? `${selectedIds.size} manually selected section(s), then filtered by the chosen review scopes.`
                        : "All sections matching the selected review scopes are included; empty sections are skipped."}
                </div>
            </div>
            <span
                style={{
                    padding: "3px 8px",
                    borderRadius: 100,
                    background: REPORT.accentSoft,
                    color: REPORT.accent,
                    fontSize: 10.5,
                    fontWeight: 650,
                    whiteSpace: "nowrap",
                }}
            >
                Planning estimate
            </span>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
            {[
                ["Sections", reviewPlan.eligible_section_count],
                ["Skipped", reviewPlan.skipped_section_count],
                ["Words", reviewPlan.total_words],
                ["Est. prompt tokens", reviewPlan.estimated_prompt_tokens],
                ["Est. completion tokens", reviewPlan.estimated_completion_tokens],
                ["Est. total tokens", reviewPlan.estimated_total_tokens],
            ].map(([label, value]) => (
                <div
                    key={label}
                    style={{
                        background: "#f6f8fa",
                        border: `1px solid ${REPORT.line}`,
                        borderRadius: 5,
                        padding: "7px 10px",
                        minWidth: 100,
                    }}
                >
                    <div style={{ fontWeight: 650, fontSize: 14, color: REPORT.ink }}>{Number(value).toLocaleString()}</div>
                    <div style={{ fontSize: 9.5, color: REPORT.inkSoft, marginTop: 1 }}>{label}</div>
                </div>
            ))}
        </div>

        <div style={{ marginTop: 8, fontSize: 10.5, color: REPORT.inkSoft }}>
            Scopes: {reviewPlan.review_scopes?.map((s) => s.label).join(" · ") || "—"}
        </div>
    </div>
)}

                    </div>
                )}

                {activeTab === "plan" && verificationMatrix && !loading && !reviewPlan && (
                    <div style={{ flex: 1, minHeight: 0, overflow: "auto", background: REPORT.panel, border: `1px solid ${REPORT.line}`, borderRadius: 8, padding: 24 }}>
                        <div style={{ fontSize: 20, fontWeight: 700, color: REPORT.accent }}>Review Plan</div>
                        <div style={{ marginTop: 8, fontSize: 13, lineHeight: 1.5, color: REPORT.inkSoft }}>Select review scopes in the left panel, optionally select specific sections, then build the plan to see the estimated review workload.</div>
                        <button onClick={buildReviewPlan} disabled={selectedReviewScopes.length === 0} style={{ marginTop: 16, background: REPORT.accent, color: "#fff", border: "none", borderRadius: 6, padding: "10px 16px", fontWeight: 650, cursor: selectedReviewScopes.length === 0 ? "not-allowed" : "pointer", opacity: selectedReviewScopes.length === 0 ? 0.6 : 1 }}>Build Review Plan</button>
                    </div>
                )}

                {showReport && (
                    <div
                        style={{
                            width: "100%",
                            maxWidth: "none",
                            height: "100%",
                            minHeight: 0,
                            margin: 0,
                            display: "flex",
                            flexDirection: "column",
                        }}
                    >
                        <header style={{ marginBottom: 12 }}>
                            <div style={{ fontSize: 20, fontWeight: 650, marginBottom: 4 }}>
                                Section Inventory
                            </div>
                            <div
                                style={{
                                    fontFamily: REPORT.mono,
                                    fontSize: 12,
                                    color: REPORT.inkSoft,
                                    wordBreak: "break-all",
                                }}
                            >
                                {wikiURL}
                            </div>
                        </header>

                        {/* Stats exactly in the spirit of render_html_report */}
                        <div
                            style={{
                                display: "flex",
                                gap: 10,
                                margin: "14px 0 16px",
                                flexWrap: "wrap",
                            }}
                        >
                            {[
                                ["Total sections", stats.total, ""],
                                ["With tables", stats.withTables, ""],
                                ["With diagrams", stats.withDiagrams, ""],
                                ["Possible issues", stats.issues, stats.issues ? "issue" : "ok"],
                            ].map(([label, value, tone]) => (
                                <div
                                    key={label}
                                    style={{
                                        background: REPORT.panel,
                                        border: `1px solid ${REPORT.line}`,
                                        borderRadius: 6,
                                        padding: "10px 14px",
                                        minWidth: 116,
                                    }}
                                >
                                    <div
                                        style={{
                                            fontSize: 20,
                                            fontWeight: 650,
                                            color:
                                                tone === "issue"
                                                    ? REPORT.issue
                                                    : tone === "ok"
                                                        ? REPORT.ok
                                                        : REPORT.ink,
                                        }}
                                    >
                                        {value}
                                    </div>
                                    <div
                                        style={{
                                            fontSize: 11.5,
                                            color: REPORT.inkSoft,
                                            marginTop: 2,
                                        }}
                                    >
                                        {label}
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Toolbar */}
                        <div
                            style={{
                                display: "flex",
                                gap: 10,
                                alignItems: "center",
                                marginBottom: 12,
                                flexWrap: "wrap",
                            }}
                        >
                            <input
                                type="search"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Filter by heading text..."
                                style={{
                                    flex: 1,
                                    minWidth: 200,
                                    padding: "8px 10px",
                                    border: `1px solid ${REPORT.line}`,
                                    borderRadius: 6,
                                    fontSize: 13.5,
                                    background: REPORT.panel,
                                    outline: "none",
                                }}
                            />
                            <select
                                value={typeFilter}
                                onChange={(e) => setTypeFilter(e.target.value)}
                                style={{
                                    padding: "8px 10px",
                                    border: `1px solid ${REPORT.line}`,
                                    borderRadius: 6,
                                    fontSize: 13.5,
                                    background: REPORT.panel,
                                }}
                            >
                                <option value="">All content types</option>
                                {Object.entries(TYPE_LABELS).map(([value, label]) => (
                                    <option key={value} value={value}>{label}</option>
                                ))}
                            </select>
                            <select
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                                style={{
                                    padding: "8px 10px",
                                    border: `1px solid ${REPORT.line}`,
                                    borderRadius: 6,
                                    fontSize: 13.5,
                                    background: REPORT.panel,
                                }}
                            >
                                <option value="">All statuses</option>
                                <option value="ok">OK</option>
                                <option value="issue">Possible issue</option>
                                <option value="empty">Empty</option>
                            </select>
                            {(searchQuery || typeFilter || statusFilter) && (
                                <button
                                    onClick={resetFilters}
                                    style={{
                                        padding: "8px 10px",
                                        border: `1px solid ${REPORT.line}`,
                                        borderRadius: 6,
                                        background: REPORT.panel,
                                        color: REPORT.inkSoft,
                                        cursor: "pointer",
                                        fontWeight: 600,
                                    }}
                                >
                                    Clear filters
                                </button>
                            )}
                        </div>

                        {matrixRows.length === 0 ? (
                            <div
                                style={{
                                    background: REPORT.panel,
                                    border: `1px solid ${REPORT.line}`,
                                    borderRadius: 8,
                                    padding: "40px 20px",
                                    textAlign: "center",
                                    color: REPORT.inkSoft,
                                    fontSize: 13.5,
                                }}
                            >
                                No sections match the current filter.
                            </div>
                        ) : (
                            <>
                                <div
                                    style={{
                                        background: REPORT.panel,
                                        border: `1px solid ${REPORT.line}`,
                                        borderRadius: 8,
                                        overflow: "hidden",
                                        minHeight: 0,
                                        flex: 1,
                                        display: "flex",
                                        flexDirection: "column",
                                    }}
                                >
                                    <div style={{ overflow: "auto", minHeight: 0, flex: 1 }}>
                                        <table
                                            style={{
                                                width: "100%",
                                                borderCollapse: "collapse",
                                                background: REPORT.panel,
                                                fontSize: 13,
                                            }}
                                        >
                                            <thead>
                                                <tr style={{ background: "#f6f8fa" }}>
                                                    <th style={{ width: 38, padding: "10px 12px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "left" }}>
                                                        <input
                                                            type="checkbox"
                                                            checked={allVisibleSelected}
                                                            onChange={toggleSelectAllVisible}
                                                        />
                                                    </th>
                                                    <th style={{ width: 42, padding: "10px 12px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "left", color: REPORT.inkSoft, fontSize: 11.5 }}>#</th>
                                                    <th style={{ width: 76, padding: "10px 12px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "left", color: REPORT.inkSoft, fontSize: 11.5 }}>No.</th>
                                                    <th style={{ padding: "10px 12px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "left", color: REPORT.inkSoft, fontSize: 11.5 }}>Section Heading</th>
                                                    <th style={{ width: 220, padding: "10px 12px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "left", color: REPORT.inkSoft, fontSize: 11.5 }}>Content Type(s)</th>
                                                    <th style={{ width: 110, padding: "10px 12px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "left", color: REPORT.inkSoft, fontSize: 11.5 }}>Status</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {matrixRows.map((row) => {
                                                    const selected = selectedIds.has(row.id);
                                                    const expanded = expandedId === row.id;
                                                    const rowBackground = row.status === "issue" ? REPORT.issueBg : REPORT.panel;

                                                    return (
                                                        <React.Fragment key={row.id}>
                                                            <tr
                                                                style={{
                                                                    background: selected ? REPORT.accentSoft : rowBackground,
                                                                    outline: selected ? `2px solid ${REPORT.accent}` : "none",
                                                                    outlineOffset: -2,
                                                                }}
                                                            >
                                                                <td style={{ padding: "10px 12px", borderBottom: `1px solid ${REPORT.line}`, verticalAlign: "top" }}>
                                                                    <input
                                                                        type="checkbox"
                                                                        checked={selected}
                                                                        onChange={() => toggleRow(row.id)}
                                                                    />
                                                                </td>
                                                                <td style={{ padding: "10px 12px", borderBottom: `1px solid ${REPORT.line}`, verticalAlign: "top", fontFamily: REPORT.mono, color: REPORT.inkSoft }}>
                                                                    {row.id}
                                                                </td>
                                                                <td style={{ padding: "10px 12px", borderBottom: `1px solid ${REPORT.line}`, verticalAlign: "top", fontFamily: REPORT.mono, color: REPORT.inkSoft }}>
                                                                    {row.numbering}
                                                                </td>
                                                                <td style={{ padding: "10px 12px", borderBottom: `1px solid ${REPORT.line}`, verticalAlign: "top" }}>
                                                                    <div
                                                                        style={{
                                                                            display: "flex",
                                                                            alignItems: "baseline",
                                                                            gap: 6,
                                                                            paddingLeft: Math.max(0, row.level - 1) * 14,
                                                                        }}
                                                                    >
                                                                        <span style={{ fontWeight: row.level === 1 ? 650 : 500 }}>
                                                                            {row.parentSection}
                                                                        </span>
                                                                    </div>
                                                                    <button
                                                                        onClick={() => setExpandedId(expanded ? null : row.id)}
                                                                        style={{
                                                                            marginTop: 6,
                                                                            padding: 0,
                                                                            border: "none",
                                                                            background: "transparent",
                                                                            color: REPORT.accent,
                                                                            fontSize: 11.5,
                                                                            cursor: "pointer",
                                                                            fontWeight: 600,
                                                                        }}
                                                                    >
                                                                        {expanded ? "Hide source segment" : `View source segment (${row.wordCount} words)`}
                                                                    </button>
                                                                </td>
                                                                <td style={{ padding: "10px 12px", borderBottom: `1px solid ${REPORT.line}`, verticalAlign: "top" }}>
                                                                    <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                                                                        {row.types.length > 0 ? row.types.map((type) => (
                                                                            <span
                                                                                key={type}
                                                                                style={{
                                                                                    display: "inline-block",
                                                                                    fontSize: 11,
                                                                                    fontWeight: 600,
                                                                                    padding: "2px 8px",
                                                                                    borderRadius: 100,
                                                                                    whiteSpace: "nowrap",
                                                                                    ...typeBadgeStyle(type),
                                                                                }}
                                                                            >
                                                                                {typeLabel(type)}
                                                                            </span>
                                                                        )) : (
                                                                            <span
                                                                                style={{
                                                                                    display: "inline-block",
                                                                                    fontSize: 11,
                                                                                    fontWeight: 600,
                                                                                    padding: "2px 8px",
                                                                                    borderRadius: 100,
                                                                                    whiteSpace: "nowrap",
                                                                                    background: REPORT.emptyBg,
                                                                                    color: REPORT.inkSoft,
                                                                                }}
                                                                            >
                                                                                None detected
                                                                            </span>
                                                                        )}
                                                                        {row.visualReviewAvailable && (
                                                                            <span
                                                                                style={{
                                                                                    display: "inline-block",
                                                                                    fontSize: 10,
                                                                                    fontWeight: 700,
                                                                                    padding: "3px 7px",
                                                                                    borderRadius: 100,
                                                                                    background: REPORT.greenBg,
                                                                                    color: REPORT.green,
                                                                                }}
                                                                            >
                                                                                VISUAL CAPTURED
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                </td>
                                                                <td style={{ padding: "10px 12px", borderBottom: `1px solid ${REPORT.line}`, verticalAlign: "top" }}>
                                                                    {statusPill(row.status)}
                                                                </td>
                                                            </tr>
                                                            {expanded && (
                                                                <tr>
                                                                    <td
                                                                        colSpan={6}
                                                                        style={{
                                                                            padding: "0 12px 12px 50px",
                                                                            borderBottom: `1px solid ${REPORT.line}`,
                                                                            background: row.status === "issue" ? "#fcf4eb" : "#fafbfc",
                                                                        }}
                                                                    >
                                                                        {row.visualEvidence.length > 0 && (
                                                                            <div style={{ marginBottom: 12 }}>
                                                                                <div style={{ fontSize: 12, fontWeight: 700, color: REPORT.ink, marginBottom: 8 }}>
                                                                                    Visual evidence captured ({row.visualEvidence.length})
                                                                                </div>
                                                                                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 10 }}>
                                                                                    {row.visualEvidence.map((visual, visualIndex) => (
                                                                                        <div key={visualIndex} style={{ border: `1px solid ${REPORT.line}`, borderRadius: 6, padding: 8, background: REPORT.panel }}>
                                                                                            <img
                                                                                                src={`${BACKEND_API_BASE}${visual.url}`}
                                                                                                alt={visual.displayName || `Section ${row.id} visual ${visualIndex + 1}`}
                                                                                                style={{ display: "block", width: "100%", maxHeight: 360, objectFit: "contain", background: "#f6f8fa", borderRadius: 4 }}
                                                                                            />
                                                                                            <div style={{ fontSize: 10.5, color: REPORT.inkSoft, marginTop: 6, wordBreak: "break-all" }}>
                                                                                                {visual.displayName || `Visual ${visualIndex + 1}`}
                                                                                            </div>
                                                                                        </div>
                                                                                    ))}
                                                                                </div>
                                                                            </div>
                                                                        )}
                                                                        <div style={{ fontSize: 11, color: REPORT.inkSoft, marginBottom: 6 }}>
                                                                            {row.visualReviewAnalyzed ? "Visual evidence reviewed by AI" : row.visualReviewAvailable ? "Visual evidence captured; AI visual review pending" : "No visual evidence captured"}
                                                                        </div>
                                                                        <pre
                                                                            style={{
                                                                                margin: 0,
                                                                                padding: 10,
                                                                                background: REPORT.panel,
                                                                                border: `1px solid ${REPORT.line}`,
                                                                                borderRadius: 6,
                                                                                fontFamily: REPORT.mono,
                                                                                fontSize: 11.5,
                                                                                lineHeight: 1.5,
                                                                                whiteSpace: "pre-wrap",
                                                                                wordBreak: "break-word",
                                                                            }}
                                                                        >
                                                                            {row.content || "No source content available."}
                                                                        </pre>
                                                                    </td>
                                                                </tr>
                                                            )}
                                                        </React.Fragment>
                                                    );
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>

                                {/* Selection bar modeled after render_html_report */}
                                {selectedIds.size > 0 && (
                                    <div
                                        style={{
                                            position: "sticky",
                                            bottom: 12,
                                            marginTop: 12,
                                            background: REPORT.ink,
                                            color: "#fff",
                                            padding: "12px 14px",
                                            display: "flex",
                                            alignItems: "center",
                                            gap: 12,
                                            fontSize: 13.5,
                                            borderRadius: 8,
                                            boxShadow: "0 -4px 16px rgba(0,0,0,0.15)",
                                        }}
                                    >
                                        <span style={{ fontWeight: 650 }}>{selectedIds.size} selected</span>
                                        <button
                                            onClick={() => { setSelectedIds(new Set()); setReviewPlan(null); }}
                                            style={{
                                                background: "transparent",
                                                color: "#cfd8e0",
                                                border: "none",
                                                textDecoration: "underline",
                                                padding: "8px 4px",
                                                cursor: "pointer",
                                                fontWeight: 600,
                                            }}
                                        >
                                            Clear selection
                                        </button>
                                        <button
                                            onClick={copySelectedHeadings}
                                            style={{
                                                marginLeft: "auto",
                                                background: "#fff",
                                                color: REPORT.ink,
                                                border: "none",
                                                borderRadius: 6,
                                                padding: "8px 14px",
                                                fontSize: 13,
                                                fontWeight: 650,
                                                cursor: "pointer",
                                            }}
                                        >
                                            Copy selected headings
                                        </button>
                                    </div>
                                )}

                                <div
                                    style={{
                                        marginTop: 14,
                                        display: "flex",
                                        justifyContent: "flex-end",
                                        gap: 8,
                                    }}
                                >
                                    <button
                                        onClick={buildReviewPlan}
                                        disabled={loading || selectedReviewScopes.length === 0}
                                        style={{
                                            background: REPORT.panel,
                                            color: REPORT.ink,
                                            padding: "10px 14px",
                                            border: `1px solid ${REPORT.line}`,
                                            borderRadius: 6,
                                            fontWeight: 650,
                                            cursor: loading || selectedReviewScopes.length === 0 ? "not-allowed" : "pointer",
                                            opacity: loading || selectedReviewScopes.length === 0 ? 0.6 : 1,
                                        }}
                                    >
                                        {loading ? "Building Review Plan..." : "Preview Review Plan"}
                                    </button>
                                    <button
                                        onClick={confirmAndTriggerLLMReview}
                                        disabled={loading || Boolean(reviewJob && ["QUEUED", "RUNNING", "CANCEL_REQUESTED"].includes(reviewJob.status)) || selectedReviewScopes.length === 0 || !verificationMatrix}
                                        style={{
                                            background: !loading && selectedReviewScopes.length > 0 && verificationMatrix ? REPORT.ok : "#cbd5e1",
                                            color: "#fff",
                                            padding: "10px 15px",
                                            border: "none",
                                            borderRadius: 6,
                                            fontWeight: 650,
                                            cursor: loading || selectedReviewScopes.length === 0 || !verificationMatrix ? "not-allowed" : "pointer",
                                            opacity: loading || selectedReviewScopes.length === 0 || !verificationMatrix ? 0.7 : 1,
                                        }}
                                    >
                                        {loading ? "Running AI Review..." : "Run AI Review →"}
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                )}


                {activeTab === "review" && verificationMatrix && (
                    <div
                        style={{
                            flex: 1,
                            minHeight: 0,
                            overflow: "auto",
                            background: REPORT.panel,
                            border: `1px solid ${REPORT.line}`,
                            borderRadius: 8,
                            padding: 24,
                        }}
                    >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
                            <div>
                                <div style={{ fontSize: 20, fontWeight: 700, color: REPORT.accent }}>AI HLD Review</div>
                                <div style={{ marginTop: 6, color: REPORT.inkSoft, fontSize: 13, lineHeight: 1.5 }}>
                                    The review is a backend-owned job. Browser refreshes do not interrupt it, and completed sections are preserved.
                                </div>
                            </div>
                            {reviewJob && ["QUEUED", "RUNNING", "CANCEL_REQUESTED"].includes(reviewJob.status) && (
                                <button onClick={cancelActiveReview} style={{ background: REPORT.issueBg, color: REPORT.issue, border: `1px solid ${REPORT.issue}`, borderRadius: 6, padding: "9px 13px", fontWeight: 700, cursor: "pointer", whiteSpace: "nowrap" }}>
                                    Stop Review
                                </button>
                            )}
                        </div>

                        {reviewJob ? (() => {
                            const p = reviewJob.progress || {};
                            const total = Number(p.total_sections || 0);
                            const completed = Number(p.completed_sections || 0);
                            const percent = total ? Math.min(100, Math.round(completed * 100 / total)) : (reviewJob.status === "COMPLETED" ? 100 : 0);
                            const usage = reviewJob.usage || {};
                            return (
                                <div style={{ marginTop: 20 }}>
                                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4,minmax(0,1fr))", gap: 10 }}>
                                        {[
                                            ["Status", reviewJob.status],
                                            ["Sections", `${completed} / ${total}`],
                                            ["Current", p.current_section_heading || "-"],
                                            ["Model calls", Number(usage.model_calls || 0).toLocaleString()],
                                        ].map(([label, value]) => (
                                            <div key={label} style={{ background: REPORT.emptyBg, border: `1px solid ${REPORT.line}`, borderRadius: 7, padding: 12 }}>
                                                <div style={{ fontSize: 17, fontWeight: 750, color: label === "Status" && reviewJob.status === "REVIEW_INCOMPLETE" ? REPORT.issue : REPORT.ink }}>{value}</div>
                                                <div style={{ marginTop: 3, fontSize: 10.5, color: REPORT.inkSoft }}>{label}</div>
                                            </div>
                                        ))}
                                    </div>
                                    <div style={{ marginTop: 18, height: 12, background: REPORT.emptyBg, borderRadius: 100, overflow: "hidden", border: `1px solid ${REPORT.line}` }}>
                                        <div style={{ height: "100%", width: `${percent}%`, background: REPORT.accent, transition: "width 300ms ease" }} />
                                    </div>
                                    <div style={{ marginTop: 7, fontSize: 11.5, color: REPORT.inkSoft }}>{percent}% complete · remaining {Math.max(0, total - completed)} section(s)</div>
                                    {p.current_section_heading && <div style={{ marginTop: 14, padding: 11, background: REPORT.accentSoft, borderRadius: 6, fontSize: 12.5, color: REPORT.ink }}><strong>Current section:</strong> {p.current_section_heading}</div>}
                                    {reviewJob.status === "RECOVERY_REQUIRED" && (
                                        <div style={{ marginTop: 14, padding: 11, background: REPORT.yellowBg, color: REPORT.yellow, borderRadius: 6, fontSize: 12.5 }}>
                                            <div>This review was interrupted by a server restart. Completed sections remain preserved.</div>
                                            <button onClick={confirmAndTriggerLLMReview} disabled={loading} style={{ marginTop: 10, background: REPORT.accent, color: "#fff", border: "none", borderRadius: 6, padding: "9px 13px", fontWeight: 700, cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.65 : 1 }}>
                                                Resume Remaining Sections →
                                            </button>
                                        </div>
                                    )}
                                    {reviewJob.error && <div style={{ marginTop: 14, padding: 11, background: REPORT.issueBg, color: REPORT.issue, borderRadius: 6, fontSize: 12.5 }}>{reviewJob.error}</div>}
                                    {reviewJob.recovery_note && <div style={{ marginTop: 14, padding: 11, background: REPORT.emptyBg, color: REPORT.inkSoft, borderRadius: 6, fontSize: 12.5 }}>{reviewJob.recovery_note}</div>}
                                    {reviewJob.status === "COMPLETED" && reviewJob.result?.segmented_blueprint && (
                                        <button onClick={() => { setAnalysisResult(reviewJob.result.segmented_blueprint); setActiveTab("findings"); }} style={{ marginTop: 18, background: REPORT.ok, color: "#fff", border: "none", borderRadius: 6, padding: "10px 16px", fontWeight: 650, cursor: "pointer" }}>
                                            View Findings →
                                        </button>
                                    )}
                                </div>
                            );
                        })() : (
                            <div style={{ marginTop: 18, padding: 16, background: REPORT.emptyBg, borderRadius: 6, color: REPORT.inkSoft, fontSize: 12.5 }}>No active HLD review job. Start a review from the Section Inventory tab.</div>
                        )}
                    </div>
                )}

                {activeTab === "findings" && analysisResult && !loading && (
                    <div
                        style={{
                            flex: 1,
                            minHeight: 0,
                            height: "100%",
                            overflowY: "auto",
                            overflowX: "hidden",
                            paddingRight: 6,
                            paddingBottom: 20,
                            scrollbarGutter: "stable",
                        }}
                    >
                        <div
                            style={{
                                width: "100%",
                                background: REPORT.panel,
                                border: `1px solid ${REPORT.line}`,
                                borderRadius: 8,
                                padding: 20,
                                boxSizing: "border-box",
                            }}
                        >
                            <div
                                style={{
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "flex-start",
                                    gap: 12,
                                    marginBottom: 16,
                                    paddingBottom: 12,
                                    borderBottom: `1px solid ${REPORT.line}`,
                                }}
                            >
                                <div>
                                    <div style={{ fontSize: 22, fontWeight: 700, color: REPORT.accent }}>
                                        AI HLD Review Results
                                    </div>
                                    <div style={{ marginTop: 4, fontSize: 12.5, color: REPORT.inkSoft }}>
                                        Evidence-based findings, passed checks, and manual-review items from the selected HLD review scopes.
                                    </div>
                                    {analysisResult.document_metadata && (
                                        <div style={{ marginTop: 6, fontSize: 11.5, color: REPORT.accent }}>
                                            {analysisResult.document_metadata.sections_reviewed ?? 0} sections reviewed · {analysisResult.document_metadata.review_scopes?.join(" · ") || "ALL"}
                                        </div>
                                    )}
                                </div>
                                <button
                                    onClick={() => { setAnalysisResult(null); setActiveTab("inventory"); }}
                                    style={{
                                        background: REPORT.emptyBg,
                                        border: `1px solid ${REPORT.line}`,
                                        color: REPORT.ink,
                                        padding: "8px 12px",
                                        borderRadius: 6,
                                        cursor: "pointer",
                                        fontSize: 12,
                                        fontWeight: 650,
                                        whiteSpace: "nowrap",
                                    }}
                                >
                                    ← Back to Section Inventory
                                </button>
                            </div>

                            {(() => {
                                const findings = Array.isArray(analysisResult.findings) ? analysisResult.findings : [];
                                const passes = Array.isArray(analysisResult.passed_checks) ? analysisResult.passed_checks : [];
                                const manual = Array.isArray(analysisResult.manual_review) ? analysisResult.manual_review : [];
                                const summary = analysisResult.review_summary || {};

                                const severityStyle = (severity) => {
                                    const value = String(severity || "Informational").toLowerCase();
                                    if (value === "critical") return { background: "#fee2e2", color: "#b91c1c" };
                                    if (value === "high") return { background: "#ffedd5", color: "#c2410c" };
                                    if (value === "medium") return { background: "#fef3c7", color: "#a16207" };
                                    if (value === "low") return { background: "#e0f2fe", color: "#0369a1" };
                                    return { background: REPORT.emptyBg, color: REPORT.inkSoft };
                                };

                                const reviewErrors = Array.isArray(analysisResult.review_errors) ? analysisResult.review_errors : [];
                                const status = summary.overall_status || (reviewErrors.length ? "REVIEW_INCOMPLETE" : findings.length ? "FINDINGS" : manual.length ? "MANUAL_REVIEW" : "PASS");
                                const statusStyle = status === "FINDINGS"
                                    ? { background: "#fff7ed", color: "#c2410c" }
                                    : status === "MANUAL_REVIEW"
                                        ? { background: "#fef3c7", color: "#a16207" }
                                        : status === "REVIEW_INCOMPLETE"
                                            ? { background: REPORT.issueBg, color: REPORT.issue }
                                            : { background: REPORT.okBg, color: REPORT.ok };

                                return (
                                    <>
                                        <div
                                            style={{
                                                display: "grid",
                                                gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
                                                gap: 10,
                                                marginBottom: 18,
                                            }}
                                        >
                                            {[
                                                ["Status", status.replace("_", " "), statusStyle],
                                                ["Findings", findings.length, findings.length ? { background: "#fff7ed", color: "#c2410c" } : { background: REPORT.okBg, color: REPORT.ok }],
                                                ["Passed checks", passes.length, { background: REPORT.okBg, color: REPORT.ok }],
                                                ["Manual review", manual.length, manual.length ? { background: "#fef3c7", color: "#a16207" } : { background: REPORT.emptyBg, color: REPORT.inkSoft }],
                                            ].map(([label, value, style]) => (
                                                <div
                                                    key={label}
                                                    style={{
                                                        border: `1px solid ${REPORT.line}`,
                                                        borderRadius: 6,
                                                        padding: "10px 12px",
                                                        background: REPORT.panel,
                                                    }}
                                                >
                                                    <div style={{ fontSize: 18, fontWeight: 700, color: style.color }}>{value}</div>
                                                    <div style={{ marginTop: 2, fontSize: 11.5, color: REPORT.inkSoft }}>{label}</div>
                                                </div>
                                            ))}
                                        </div>

                                        {reviewErrors.length > 0 && (
                                            <section
                                                style={{
                                                    marginBottom: 20,
                                                    border: "1px solid #fecaca",
                                                    borderRadius: 7,
                                                    background: "#fff7f7",
                                                    padding: 14,
                                                }}
                                            >
                                                <h4 style={{ margin: 0, color: "#b91c1c", fontSize: 18 }}>Review Errors</h4>
                                                <div style={{ marginTop: 6, fontSize: 11.5, color: REPORT.inkSoft }}>
                                                    These sections did not complete successfully and are not counted as PASS.
                                                </div>
                                                <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 8 }}>
                                                    {reviewErrors.map((item, idx) => (
                                                        <div key={idx} style={{ border: "1px solid #fecaca", borderRadius: 6, padding: 10, background: "#fff" }}>
                                                            <div style={{ fontWeight: 700, color: REPORT.ink }}>{item.section || `Section ${item.section_id || "?"}`}</div>
                                                            <div style={{ marginTop: 4, fontSize: 11.5, color: "#991b1b", whiteSpace: "pre-wrap" }}>{item.error || "Unknown review error"}</div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </section>
                                        )}

                                        {(() => {
                                            const consumption = analysisResult.ai_consumption || {};
                                            const totals = consumption.totals || {};
                                            const bySection = Array.isArray(consumption.by_section) ? consumption.by_section : [];
                                            const byScope = consumption.by_scope && typeof consumption.by_scope === "object" ? consumption.by_scope : {};
                                            const byModel = consumption.by_model && typeof consumption.by_model === "object" ? consumption.by_model : {};
                                            const fmt = (value) => Number(value || 0).toLocaleString();
                                            const fmtCredit = (value) => Number(value || 0).toFixed(6);
                                            const fmtSeconds = (value) => `${(Number(value || 0) / 1000).toFixed(1)}s`;
                                            const scopeEntries = Object.entries(byScope);
                                            const modelEntries = Object.entries(byModel);

                                            return (
                                                <section
                                                    style={{
                                                        marginBottom: 20,
                                                        border: `1px solid ${REPORT.line}`,
                                                        borderRadius: 7,
                                                        background: REPORT.panel,
                                                        padding: 14,
                                                    }}
                                                >
                                                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, marginBottom: 6 }}>
                                                        <div>
                                                            <h4 style={{ margin: 0, color: REPORT.accent, fontSize: 18 }}>AI Consumption</h4>
                                                            <div style={{ marginTop: 3, fontSize: 11.5, color: REPORT.inkSoft }}>
                                                                Actual Copilot SDK usage captured per section. One Copilot turn covers all selected scopes for that section; usage is not artificially split by scope.
                                                            </div>
                                                        </div>
                                                        <div style={{ fontSize: 10.5, color: REPORT.inkSoft, textAlign: "right" }}>
                                                            AI credits shown below are derived from the SDK's <code style={{ fontSize: 10 }}>totalNanoAiu</code>.
                                                        </div>
                                                    </div>

                                                    <div
                                                        style={{
                                                            display: "grid",
                                                            gridTemplateColumns: "repeat(5, minmax(0, 1fr))",
                                                            gap: 8,
                                                            marginTop: 12,
                                                        }}
                                                    >
                                                        {[
                                                            ["Model calls", fmt(totals.model_calls)],
                                                            ["Input tokens", fmt(totals.input_tokens)],
                                                            ["Output tokens", fmt(totals.output_tokens)],
                                                            ["Reasoning tokens", fmt(totals.reasoning_tokens)],
                                                            ["SDK AI credits", fmtCredit(totals.ai_credits_from_nano_aiu)],
                                                        ].map(([label, value]) => (
                                                            <div key={label} style={{ border: `1px solid ${REPORT.line}`, borderRadius: 6, padding: "9px 10px", background: REPORT.emptyBg }}>
                                                                <div style={{ fontSize: 16, fontWeight: 700, color: REPORT.ink }}>{value}</div>
                                                                <div style={{ marginTop: 2, fontSize: 10.5, color: REPORT.inkSoft }}>{label}</div>
                                                            </div>
                                                        ))}
                                                    </div>

                                                    {bySection.length > 0 && (
                                                        <div style={{ marginTop: 14 }}>
                                                            <div style={{ fontSize: 12.5, fontWeight: 700, color: REPORT.ink, marginBottom: 6 }}>Per-section usage details</div>
                                                            <div style={{ overflowX: "auto" }}>
                                                                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11.2 }}>
                                                                    <thead>
                                                                        <tr style={{ background: REPORT.emptyBg }}>
                                                                            {["Section", "Models", "Input", "Output", "Reasoning", "AI credits", "Context"].map((label) => (
                                                                                <th key={label} style={{ textAlign: label === "Section" ? "left" : "right", padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, color: REPORT.inkSoft }}>{label}</th>
                                                                            ))}
                                                                        </tr>
                                                                    </thead>
                                                                    <tbody>
                                                                        {bySection.map((item, idx) => {
                                                                            const ci = item.contextInfo || {};
                                                                            return (
                                                                                <tr key={`${item.sectionId || idx}-${idx}`}>
                                                                                    <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, fontWeight: 650, textAlign: "left" }}>{item.sectionHeading || `Section ${item.sectionId || "?"}`}</td>
                                                                                    <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{Array.isArray(item.models) ? item.models.join(", ") : "-"}</td>
                                                                                    <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.inputTokens)}</td>
                                                                                    <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.outputTokens)}</td>
                                                                                    <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.reasoningTokens)}</td>
                                                                                    <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmtCredit(item.aiCreditsFromNanoAiu)}</td>
                                                                                    <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{ci.totalTokens ? `${fmt(ci.totalTokens)} / ${fmt(ci.promptTokenLimit)}` : "-"}</td>
                                                                                </tr>
                                                                            );
                                                                        })}
                                                                    </tbody>
                                                                </table>
                                                            </div>
                                                        </div>
                                                    )}

                                                    {scopeEntries.length > 0 && (
                                                        <div style={{ marginTop: 14 }}>
                                                            <div style={{ fontSize: 12.5, fontWeight: 700, color: REPORT.ink, marginBottom: 6 }}>Review scope coverage</div>
                                                            <div style={{ marginBottom: 7, fontSize: 10.5, color: REPORT.inkSoft }}>Tokens and AI credits are not split across scopes because the model receives all selected scopes in one section-level turn.</div>
                                                            <div style={{ overflowX: "auto" }}>
                                                                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11.5 }}>
                                                                    <thead>
                                                                        <tr style={{ background: REPORT.emptyBg }}>
                                                                            {[["Scope", "left"], ["Sections", "right"], ["Shared calls", "right"]].map(([label, align]) => (
                                                                                <th key={label} style={{ textAlign: align, padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, color: REPORT.inkSoft }}>{label}</th>
                                                                            ))}
                                                                        </tr>
                                                                    </thead>
                                                                    <tbody>
                                                                        {scopeEntries.map(([scope, item]) => (
                                                                            <tr key={scope}>
                                                                                <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, fontWeight: 650 }}>{scope}</td>
                                                                                <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.sections_reviewed)}</td>
                                                                                <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.shared_model_calls)}</td>
                                                                            </tr>
                                                                        ))}
                                                                    </tbody>
                                                                </table>
                                                            </div>
                                                        </div>
                                                    )}

                                                    {modelEntries.length > 0 && (
                                                        <div style={{ marginTop: 14 }}>
                                                            <div style={{ fontSize: 12.5, fontWeight: 700, color: REPORT.ink, marginBottom: 6 }}>By model</div>
                                                            <div style={{ overflowX: "auto" }}>
                                                                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11.5 }}>
                                                                    <thead>
                                                                        <tr style={{ background: REPORT.emptyBg }}>
                                                                            {[["Model", "left"], ["Calls", "right"], ["Input", "right"], ["Output", "right"], ["Reasoning", "right"], ["AI credits", "right"]].map(([label, align]) => (
                                                                                <th key={label} style={{ textAlign: align, padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, color: REPORT.inkSoft }}>{label}</th>
                                                                            ))}
                                                                        </tr>
                                                                    </thead>
                                                                    <tbody>
                                                                        {modelEntries.map(([model, item]) => (
                                                                            <tr key={model}>
                                                                                <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, fontWeight: 650 }}>{model}</td>
                                                                                <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.calls)}</td>
                                                                                <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.input_tokens)}</td>
                                                                                <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.output_tokens)}</td>
                                                                                <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.reasoning_tokens)}</td>
                                                                                <td style={{ padding: "7px 8px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmtCredit(item.ai_credits_from_nano_aiu)}</td>
                                                                            </tr>
                                                                        ))}
                                                                    </tbody>
                                                                </table>
                                                            </div>
                                                        </div>
                                                    )}

                                                    {bySection.length > 0 && (
                                                        <details style={{ marginTop: 14 }}>
                                                            <summary style={{ cursor: "pointer", fontSize: 12.5, fontWeight: 700, color: REPORT.accent }}>Exact per-section usage ({bySection.length})</summary>
                                                            <div style={{ marginTop: 8, overflowX: "auto" }}>
                                                                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                                                                    <thead>
                                                                        <tr style={{ background: REPORT.emptyBg }}>
                                                                            {[["Section", "left"], ["Scope", "left"], ["Model", "left"], ["Input", "right"], ["Output", "right"], ["Reasoning", "right"], ["Total", "right"], ["AI credits", "right"], ["Visual", "center"]].map(([label, align]) => (
                                                                                <th key={label} style={{ textAlign: align, padding: "6px 7px", borderBottom: `1px solid ${REPORT.line}`, color: REPORT.inkSoft }}>{label}</th>
                                                                            ))}
                                                                        </tr>
                                                                    </thead>
                                                                    <tbody>
                                                                        {bySection.map((item, idx) => (
                                                                            <tr key={`${item.sectionId}-${item.reviewScope}-${idx}`}>
                                                                                <td style={{ padding: "6px 7px", borderBottom: `1px solid ${REPORT.line}`, maxWidth: 280 }}>{item.sectionHeading || `Section ${item.sectionId}`}</td>
                                                                                <td style={{ padding: "6px 7px", borderBottom: `1px solid ${REPORT.line}` }}>{Array.isArray(item.reviewScopes) ? item.reviewScopes.join(", ") : (item.reviewScope || "—")}</td>
                                                                                <td style={{ padding: "6px 7px", borderBottom: `1px solid ${REPORT.line}` }}>{Array.isArray(item.models) ? item.models.join(", ") : "—"}</td>
                                                                                <td style={{ padding: "6px 7px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.inputTokens)}</td>
                                                                                <td style={{ padding: "6px 7px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.outputTokens)}</td>
                                                                                <td style={{ padding: "6px 7px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.reasoningTokens)}</td>
                                                                                <td style={{ padding: "6px 7px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmt(item.totalTokens)}</td>
                                                                                <td style={{ padding: "6px 7px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "right" }}>{fmtCredit(item.aiCreditsFromNanoAiu)}</td>
                                                                                <td style={{ padding: "6px 7px", borderBottom: `1px solid ${REPORT.line}`, textAlign: "center" }}>{item.visualReviewed ? "Yes" : "No"}</td>
                                                                            </tr>
                                                                        ))}
                                                                    </tbody>
                                                                </table>
                                                            </div>
                                                        </details>
                                                    )}

                                                    <div style={{ marginTop: 10, fontSize: 10.5, color: REPORT.empty }}>
                                                        Duration: {fmtSeconds(totals.duration_ms)} · Cache read: {fmt(totals.cache_read_tokens)} · Cache write: {fmt(totals.cache_write_tokens)} · Premium request cost: {fmtCredit(totals.premium_request_cost)}
                                                    </div>
                                                </section>
                                            );
                                        })()}

                                        <section>
                                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                                                <h4 style={{ margin: 0, color: REPORT.accent, fontSize: 18 }}>Review Findings</h4>
                                                <span
                                                    style={{
                                                        display: "inline-flex",
                                                        alignItems: "center",
                                                        padding: "4px 9px",
                                                        borderRadius: 100,
                                                        fontSize: 11.5,
                                                        fontWeight: 650,
                                                        ...statusStyle,
                                                    }}
                                                >
                                                    {status.replace("_", " ")}
                                                </span>
                                            </div>

                                            {findings.length > 0 ? findings.map((finding, idx) => {
                                                const sev = severityStyle(finding.severity);
                                                return (
                                                    <article
                                                        key={finding.finding_id || idx}
                                                        style={{
                                                            border: `1px solid ${REPORT.line}`,
                                                            borderLeft: `4px solid ${sev.color}`,
                                                            borderRadius: 7,
                                                            padding: 14,
                                                            marginBottom: 10,
                                                            background: REPORT.panel,
                                                        }}
                                                    >
                                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
                                                            <div>
                                                                <div style={{ fontSize: 13.5, fontWeight: 700, color: REPORT.ink }}>
                                                                    {finding.finding_id ? `${finding.finding_id} · ` : ""}{finding.title || "Review finding"}
                                                                </div>
                                                                <div style={{ marginTop: 3, fontSize: 11.5, color: REPORT.accent }}>
                                                                    {finding.scope || "General"}{finding.category ? ` · ${finding.category}` : ""}
                                                                </div>
                                                            </div>
                                                            <span style={{ background: sev.background, color: sev.color, padding: "3px 9px", borderRadius: 100, fontSize: 11.5, fontWeight: 700, whiteSpace: "nowrap" }}>
                                                                {finding.severity || "Informational"}
                                                            </span>
                                                        </div>

                                                        <div style={{ marginTop: 10, fontSize: 12.5, lineHeight: 1.55, color: REPORT.ink }}>
                                                            <strong>Finding:</strong> {finding.finding || ""}
                                                        </div>

                                                        {finding.evidence && (
                                                            <div style={{ marginTop: 9, background: "#f6f8fa", border: `1px solid ${REPORT.line}`, borderRadius: 5, padding: 9 }}>
                                                                <div style={{ fontSize: 11.5, fontWeight: 700, color: REPORT.inkSoft, marginBottom: 4 }}>Evidence</div>
                                                                {finding.evidence.text && <div style={{ fontSize: 11.5, color: REPORT.inkSoft }}><strong>Text:</strong> {finding.evidence.text}</div>}
                                                                {finding.evidence.visual_observation && <div style={{ marginTop: 4, fontSize: 11.5, color: REPORT.inkSoft }}><strong>Visual:</strong> {finding.evidence.visual_observation}</div>}
                                                            </div>
                                                        )}

                                                        {finding.impact && <div style={{ marginTop: 9, fontSize: 12, color: REPORT.inkSoft }}><strong>Impact:</strong> {finding.impact}</div>}
                                                        {finding.recommendation && <div style={{ marginTop: 6, fontSize: 12, color: REPORT.inkSoft }}><strong>Recommendation:</strong> {finding.recommendation}</div>}
                                                        <div style={{ marginTop: 8, fontSize: 10.5, color: REPORT.empty }}>
                                                            Confidence: {typeof finding.confidence === "number" ? finding.confidence.toFixed(2) : "—"} · Visual reviewed: {finding.visual_reviewed ? "Yes" : "No"}
                                                        </div>
                                                    </article>
                                                );
                                            }) : (
                                                <div style={{ padding: 16, border: `1px solid ${REPORT.line}`, borderRadius: 6, background: REPORT.okBg, color: REPORT.ok, fontSize: 12.5 }}>
                                                    No evidence-supported findings were identified for the selected review scopes.
                                                </div>
                                            )}
                                        </section>

                                        <section style={{ marginTop: 20 }}>
                                            <h4 style={{ margin: "0 0 10px", color: REPORT.ok, fontSize: 18 }}>Passed Checks</h4>
                                            {passes.length > 0 ? passes.map((check, idx) => (
                                                <div key={idx} style={{ border: `1px solid ${REPORT.line}`, borderRadius: 6, padding: 11, marginBottom: 7, background: REPORT.panel }}>
                                                    <div style={{ fontSize: 12.5, fontWeight: 700, color: REPORT.ink }}>{check.scope || "General"}{check.category ? ` · ${check.category}` : ""}</div>
                                                    <div style={{ marginTop: 3, fontSize: 12, color: REPORT.inkSoft }}><strong>Check:</strong> {check.check || ""}</div>
                                                    {check.evidence && <div style={{ marginTop: 3, fontSize: 11.5, color: REPORT.inkSoft }}><strong>Evidence:</strong> {check.evidence}</div>}
                                                </div>
                                            )) : (
                                                <div style={{ color: REPORT.empty, fontSize: 12.5, fontStyle: "italic" }}>No positive checks were returned.</div>
                                            )}
                                        </section>

                                        <section style={{ marginTop: 20 }}>
                                            <h4 style={{ margin: "0 0 10px", color: REPORT.yellow, fontSize: 18 }}>Manual Review Required</h4>
                                            {manual.length > 0 ? manual.map((item, idx) => (
                                                <div key={idx} style={{ border: `1px solid ${REPORT.line}`, borderRadius: 6, padding: 11, marginBottom: 7, background: "#fffbeb" }}>
                                                    <div style={{ fontSize: 12.5, fontWeight: 700, color: REPORT.ink }}>{item.scope || "General"}</div>
                                                    <div style={{ marginTop: 3, fontSize: 12, color: REPORT.inkSoft }}><strong>Reason:</strong> {item.reason || ""}</div>
                                                    {item.required_action && <div style={{ marginTop: 3, fontSize: 11.5, color: REPORT.inkSoft }}><strong>Required action:</strong> {item.required_action}</div>}
                                                </div>
                                            )) : (
                                                <div style={{ color: REPORT.empty, fontSize: 12.5, fontStyle: "italic" }}>No manual validation items were identified.</div>
                                            )}
                                        </section>
                                    </>
                                );
                            })()}
                        </div>
                    </div>
                )}
                {activeTab === "telemetry" && analysisResult && !loading && (
                    <div style={{ flex: 1, minHeight: 0, overflowY: "auto", overflowX: "hidden", paddingRight: 6, scrollbarGutter: "stable" }}>
                        <div style={{ background: REPORT.panel, border: `1px solid ${REPORT.line}`, borderRadius: 8, padding: 22 }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 14, marginBottom: 16 }}>
                                <div>
                                    <h2 style={{ margin: 0, color: REPORT.accent, fontSize: 25 }}>AI Consumption & Telemetry</h2>
                                    <p style={{ margin: "6px 0 0", color: REPORT.inkSoft, fontSize: 12.5 }}>Final workflow step. Review actual Copilot usage and request/context diagnostics.</p>
                                </div>
                                <button onClick={downloadExcelReport} disabled={exportingExcel} style={{ background: REPORT.accent, color: "#fff", border: "none", borderRadius: 7, padding: "10px 16px", fontWeight: 700, cursor: exportingExcel ? "not-allowed" : "pointer", opacity: exportingExcel ? 0.65 : 1, whiteSpace: "nowrap" }}>
                                    {exportingExcel ? "Building Excel..." : "Download Excel Report"}
                                </button>
                            </div>
                            {excelExportError && <div style={{ marginBottom: 12, padding: 10, borderRadius: 6, background: REPORT.issueBg, color: REPORT.issue, fontSize: 12 }}>{excelExportError}</div>}
                            {(() => {
                                const c = analysisResult.ai_consumption || {};
                                const t = c.totals || {};
                                const secs = c.by_section || [];
                                const scopes = Object.entries(c.by_scope || {});
                                const models = Object.entries(c.by_model || {});
                                const tiers = Object.entries(c.by_auto_tier || {});
                                const fmt = v => Number(v || 0).toLocaleString();
                                const credits = v => Number(v || 0).toFixed(6);
                                return <>
                                    <div style={{ display: "grid", gridTemplateColumns: "repeat(5, minmax(0,1fr))", gap: 10, marginBottom: 18 }}>
                                        {[["Model calls",t.model_calls],["Input tokens",t.input_tokens],["Output tokens",t.output_tokens],["Reasoning tokens",t.reasoning_tokens],["SDK AI credits",credits(t.ai_credits_from_nano_aiu)]].map(([label,value]) => <div key={label} style={{ background: REPORT.emptyBg, border: `1px solid ${REPORT.line}`, borderRadius: 7, padding: 12 }}><div style={{ fontSize: 20, fontWeight: 750 }}>{typeof value === "string" ? value : fmt(value)}</div><div style={{ marginTop: 3, fontSize: 10.5, color: REPORT.inkSoft }}>{label}</div></div>)}
                                    </div>
                                    <div style={{
                                        display: "grid",
                                        gridTemplateColumns: "1fr 1fr 1fr",
                                        gap: 12,
                                        marginBottom: 18,
                                    }}>
                                        <div style={{ background: REPORT.accentSoft, border: `1px solid ${REPORT.line}`, borderRadius: 7, padding: 12 }}>
                                            <div style={{ fontSize: 12, fontWeight: 750, color: REPORT.accent, marginBottom: 5 }}>Application routing</div>
                                            <div style={{ fontSize: 11.5, color: REPORT.inkSoft, lineHeight: 1.45 }}>
                                                The platform selects an <b>Auto tier</b> from evidence complexity. GitHub Copilot Auto selects the concrete model.
                                            </div>
                                        </div>
                                        <div style={{ background: REPORT.emptyBg, border: `1px solid ${REPORT.line}`, borderRadius: 7, padding: 12 }}>
                                            <div style={{ fontSize: 12, fontWeight: 750, marginBottom: 5 }}>Auto tiers used</div>
                                            <div style={{ fontSize: 11.5, color: REPORT.inkSoft }}>
                                                {tiers.length ? tiers.map(([tier, item]) => `${tier}: ${fmt(item.sections_reviewed)}`).join("  ·  ") : "No completed routing records"}
                                            </div>
                                        </div>
                                        <div style={{ background: REPORT.emptyBg, border: `1px solid ${REPORT.line}`, borderRadius: 7, padding: 12 }}>
                                            <div style={{ fontSize: 12, fontWeight: 750, marginBottom: 5 }}>Actual models</div>
                                            <div style={{ fontSize: 11.5, color: REPORT.inkSoft }}>
                                                {models.length ? models.map(([model, item]) => `${model}: ${fmt(item.calls)}`).join("  ·  ") : "No completed model calls"}
                                            </div>
                                        </div>
                                    </div>
                                    <div style={{ overflowX: "auto", marginBottom: 18 }}>
                                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                                            <thead><tr style={{ background: REPORT.emptyBg }}>{["Section","Scopes","Mode","Auto tier","Actual model","Input","Output","Reasoning","AI credits","Src est.","Prompt est.","Attachments","Context","Status"].map(h=><th key={h} style={{ padding: "7px 8px", textAlign: ["Input","Output","Reasoning","AI credits","Src est.","Prompt est.","Attachments","Context"].includes(h)?"right":"left", borderBottom:`1px solid ${REPORT.line}`, color:REPORT.inkSoft }}>{h}</th>)}</tr></thead>
                                            <tbody>{secs.map((item,idx)=>{const d=item.diagnostics||{}; const ci=item.contextInfo||{}; return <tr key={`${item.sectionId}-${idx}`}><td style={{padding:"7px 8px",borderBottom:`1px solid ${REPORT.line}`}}>{item.sectionHeading||`Section ${item.sectionId}`}</td><td style={{padding:"7px 8px",borderBottom:`1px solid ${REPORT.line}`}}>{(item.reviewScopes||[]).join(", ")}</td><td style={{padding:"7px 8px",borderBottom:`1px solid ${REPORT.line}`}}>{item.routing?.requestedModelMode||"auto"}</td><td style={{padding:"7px 8px",borderBottom:`1px solid ${REPORT.line}`}}>{item.routing?.requestedAutoTier||"default"}</td><td style={{padding:"7px 8px",borderBottom:`1px solid ${REPORT.line}`}}>{item.routing?.actualModel||(item.models||[]).join(", ")||"-"}</td><td style={{padding:"7px 8px",textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(item.inputTokens)}</td><td style={{padding:"7px 8px",textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(item.outputTokens)}</td><td style={{padding:"7px 8px",textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(item.reasoningTokens)}</td><td style={{padding:"7px 8px",textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{credits(item.aiCreditsFromNanoAiu)}</td><td style={{padding:"7px 8px",textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(d.sourceEstimatedTokens)}</td><td style={{padding:"7px 8px",textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(d.promptEstimatedTokens)}</td><td style={{padding:"7px 8px",textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(d.attachmentCount)}</td><td style={{padding:"7px 8px",textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(ci.totalTokens)}</td><td style={{padding:"7px 8px",borderBottom:`1px solid ${REPORT.line}`}}>{item.turnStatus||"-"}</td></tr>})}</tbody>
                                        </table>
                                    </div>
                                    <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:18 }}>
                                        <div><h3 style={{margin:"0 0 8px",fontSize:15}}>Scope coverage</h3><table style={{width:"100%",borderCollapse:"collapse",fontSize:11.5}}><thead><tr style={{background:REPORT.emptyBg}}><th style={{padding:7,textAlign:"left"}}>Scope</th><th style={{padding:7,textAlign:"right"}}>Sections</th><th style={{padding:7,textAlign:"right"}}>Shared calls</th></tr></thead><tbody>{scopes.map(([scope,item])=><tr key={scope}><td style={{padding:7,borderBottom:`1px solid ${REPORT.line}`}}>{scope}</td><td style={{padding:7,textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(item.sections_reviewed)}</td><td style={{padding:7,textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(item.shared_model_calls)}</td></tr>)}</tbody></table></div>
                                        <div><h3 style={{margin:"0 0 8px",fontSize:15}}>Model usage</h3><table style={{width:"100%",borderCollapse:"collapse",fontSize:11.5}}><thead><tr style={{background:REPORT.emptyBg}}><th style={{padding:7,textAlign:"left"}}>Model</th><th style={{padding:7,textAlign:"right"}}>Calls</th><th style={{padding:7,textAlign:"right"}}>Input</th><th style={{padding:7,textAlign:"right"}}>AI credits</th></tr></thead><tbody>{models.map(([model,item])=><tr key={model}><td style={{padding:7,borderBottom:`1px solid ${REPORT.line}`}}>{model}</td><td style={{padding:7,textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(item.calls)}</td><td style={{padding:7,textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(item.input_tokens)}</td><td style={{padding:7,textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{credits(item.ai_credits_from_nano_aiu)}</td></tr>)}</tbody></table></div>
                                        <div><h3 style={{margin:"0 0 8px",fontSize:15}}>Auto routing</h3><table style={{width:"100%",borderCollapse:"collapse",fontSize:11.5}}><thead><tr style={{background:REPORT.emptyBg}}><th style={{padding:7,textAlign:"left"}}>Tier</th><th style={{padding:7,textAlign:"right"}}>Sections</th><th style={{padding:7,textAlign:"right"}}>Calls</th></tr></thead><tbody>{tiers.map(([tier,item])=><tr key={tier}><td style={{padding:7,borderBottom:`1px solid ${REPORT.line}`}}>{tier}</td><td style={{padding:7,textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(item.sections_reviewed)}</td><td style={{padding:7,textAlign:"right",borderBottom:`1px solid ${REPORT.line}`}}>{fmt(item.model_calls)}</td></tr>)}</tbody></table></div>
                                    </div>
                                    <div style={{marginTop:16,padding:10,background:REPORT.accentSoft,border:`1px solid ${REPORT.line}`,borderRadius:6,color:REPORT.inkSoft,fontSize:11.5,lineHeight:1.45}}>Actual model usage comes from Copilot SDK telemetry. Source/prompt estimates are diagnostics only. A shared section-level call is not artificially split across review scopes.</div>
                                </>;
                            })()}
                        </div>
                    </div>
                )}
            </main>
        </section>
    );
}
