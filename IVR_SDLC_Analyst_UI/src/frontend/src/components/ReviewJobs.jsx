import React, { useEffect, useMemo, useState } from "react";
import {
    listReviewJobs,
    deleteReviewJob,
    clearCompletedReviewJobs,
} from "../services/api";

const COLORS = {
    ink: "#16212e",
    soft: "#4a5a6b",
    line: "#d9e0e7",
    panel: "#ffffff",
    bg: "#eef1f4",
    accent: "#2a5b8c",
    accentSoft: "#e4edf6",
    ok: "#2f7d4f",
    okBg: "#e5f3ea",
    issue: "#b4570a",
    issueBg: "#fbead9",
    muted: "#eef0f2",
    mono: "SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace",
    sans: "-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
};

function formatDate(value) {
    if (!value) return "-";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function formatDuration(seconds) {
    const total = Number(seconds || 0);
    if (!total) return "-";
    if (total < 60) return `${total.toFixed(1)}s`;
    const mins = Math.floor(total / 60);
    const secs = Math.round(total % 60);
    return `${mins}m ${secs}s`;
}

function formatCredits(value) {
    return Number(value || 0).toFixed(4);
}

function statusStyle(status) {
    switch (status) {
        case "COMPLETED":
            return { background: COLORS.okBg, color: COLORS.ok };
        case "FAILED":
        case "RECOVERY_REQUIRED":
            return { background: COLORS.issueBg, color: COLORS.issue };
        case "CANCELLED":
            return { background: COLORS.muted, color: COLORS.soft };
        default:
            return { background: COLORS.accentSoft, color: COLORS.accent };
    }
}

export default function ReviewJobs({ onOpenJob }) {
    const [jobs, setJobs] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [search, setSearch] = useState("");
    const [status, setStatus] = useState("");
    const [selected, setSelected] = useState(new Set());
    const [refreshTick, setRefreshTick] = useState(0);

    async function loadJobs() {
        setLoading(true);
        setError("");
        try {
            const data = await listReviewJobs({
                search: search.trim(),
                status,
                limit: 200,
                offset: 0,
            });
            setJobs(Array.isArray(data.jobs) ? data.jobs : []);
            setTotal(Number(data.total || 0));
            setSelected(new Set());
        } catch (err) {
            setError(err.message || "Failed to load review jobs.");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadJobs();
    }, [status, refreshTick]);

    const completedJobs = useMemo(
        () => jobs.filter((job) => job.status === "COMPLETED"),
        [jobs]
    );

    const allCompletedSelected =
        completedJobs.length > 0 &&
        completedJobs.every((job) => selected.has(job.job_id));

    function toggleSelected(jobId) {
        setSelected((previous) => {
            const next = new Set(previous);
            if (next.has(jobId)) next.delete(jobId);
            else next.add(jobId);
            return next;
        });
    }

    function toggleAllCompleted() {
        setSelected((previous) => {
            const next = new Set(previous);
            if (allCompletedSelected) {
                completedJobs.forEach((job) => next.delete(job.job_id));
            } else {
                completedJobs.forEach((job) => next.add(job.job_id));
            }
            return next;
        });
    }

    async function removeJob(job) {
        if (!window.confirm(`Delete review job ${job.job_id}?`)) return;
        try {
            await deleteReviewJob(job.job_id);
            await loadJobs();
        } catch (err) {
            setError(err.message || "Unable to delete the review job.");
        }
    }

    async function removeSelectedCompleted() {
        const ids = Array.from(selected).filter((id) =>
            completedJobs.some((job) => job.job_id === id)
        );
        if (!ids.length) return;
        if (!window.confirm(`Delete ${ids.length} completed review job(s)?`)) return;
        try {
            await clearCompletedReviewJobs(ids);
            await loadJobs();
        } catch (err) {
            setError(err.message || "Unable to delete the selected completed jobs.");
        }
    }

    async function removeAllCompleted() {
        if (!completedJobs.length) return;
        if (!window.confirm(`Delete all ${completedJobs.length} completed job(s) shown?`)) return;
        try {
            await clearCompletedReviewJobs();
            await loadJobs();
        } catch (err) {
            setError(err.message || "Unable to clear completed jobs.");
        }
    }

    return (
        <section
            style={{
                width: "100%",
                height: "100%",
                minHeight: 0,
                overflow: "hidden",
                boxSizing: "border-box",
                background: COLORS.bg,
                padding: 20,
                fontFamily: COLORS.sans,
                color: COLORS.ink,
                display: "flex",
                flexDirection: "column",
            }}
        >
            <header style={{ marginBottom: 14 }}>
                <div style={{ fontSize: 24, fontWeight: 700, color: COLORS.accent }}>
                    Review Jobs
                </div>
                <div style={{ marginTop: 4, fontSize: 12.5, color: COLORS.soft }}>
                    Persistent technical-document review history. Select a job to inspect its findings or telemetry.
                </div>
            </header>

            <div
                style={{
                    background: COLORS.panel,
                    border: `1px solid ${COLORS.line}`,
                    borderRadius: 8,
                    padding: 12,
                    marginBottom: 12,
                    display: "flex",
                    gap: 10,
                    alignItems: "center",
                    flexWrap: "wrap",
                }}
            >
                <input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    onKeyDown={(event) => {
                        if (event.key === "Enter") setRefreshTick((value) => value + 1);
                    }}
                    placeholder="Search job, document or URL..."
                    style={{
                        flex: 1,
                        minWidth: 280,
                        padding: "9px 10px",
                        border: `1px solid ${COLORS.line}`,
                        borderRadius: 6,
                        fontSize: 12.5,
                    }}
                />
                <select
                    value={status}
                    onChange={(event) => setStatus(event.target.value)}
                    style={{
                        padding: "9px 10px",
                        border: `1px solid ${COLORS.line}`,
                        borderRadius: 6,
                        fontSize: 12.5,
                        background: COLORS.panel,
                    }}
                >
                    <option value="">All statuses</option>
                    <option value="PENDING">Pending</option>
                    <option value="QUEUED">Queued</option>
                    <option value="RUNNING">In Progress</option>
                    <option value="COMPLETED">Completed</option>
                    <option value="FAILED">Failed</option>
                    <option value="CANCELLED">Cancelled</option>
                    <option value="RECOVERY_REQUIRED">Recovery Required</option>
                </select>
                <button
                    onClick={() => setRefreshTick((value) => value + 1)}
                    disabled={loading}
                    style={{
                        padding: "9px 12px",
                        background: COLORS.accent,
                        color: "#fff",
                        border: "none",
                        borderRadius: 6,
                        fontWeight: 700,
                        cursor: loading ? "not-allowed" : "pointer",
                    }}
                >
                    {loading ? "Refreshing..." : "Refresh"}
                </button>
                <button
                    onClick={removeSelectedCompleted}
                    disabled={!Array.from(selected).some((id) => completedJobs.some((job) => job.job_id === id))}
                    style={{
                        padding: "9px 12px",
                        background: COLORS.panel,
                        color: COLORS.issue,
                        border: `1px solid ${COLORS.issue}`,
                        borderRadius: 6,
                        fontWeight: 700,
                        cursor: "pointer",
                        opacity: Array.from(selected).some((id) => completedJobs.some((job) => job.job_id === id)) ? 1 : 0.5,
                    }}
                >
                    Delete Selected
                </button>
                <button
                    onClick={removeAllCompleted}
                    disabled={!completedJobs.length}
                    style={{
                        padding: "9px 12px",
                        background: COLORS.panel,
                        color: COLORS.soft,
                        border: `1px solid ${COLORS.line}`,
                        borderRadius: 6,
                        fontWeight: 700,
                        cursor: "pointer",
                        opacity: completedJobs.length ? 1 : 0.5,
                    }}
                >
                    Clear Completed
                </button>
            </div>

            {error && (
                <div
                    style={{
                        marginBottom: 12,
                        padding: 10,
                        borderRadius: 6,
                        background: COLORS.issueBg,
                        border: `1px solid ${COLORS.issue}`,
                        color: COLORS.issue,
                        fontSize: 12,
                    }}
                >
                    {error}
                </div>
            )}

            <div
                style={{
                    background: COLORS.panel,
                    border: `1px solid ${COLORS.line}`,
                    borderRadius: 8,
                    overflow: "hidden",
                    minHeight: 0,
                    flex: 1,
                    display: "flex",
                    flexDirection: "column",
                }}
            >
                <div style={{ padding: "10px 12px", borderBottom: `1px solid ${COLORS.line}`, fontSize: 12, color: COLORS.soft }}>
                    {total.toLocaleString()} review job(s)
                </div>

                <div style={{ overflow: "auto", minHeight: 0, flex: 1 }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11.5 }}>
                        <thead>
                            <tr style={{ background: "#f6f8fa", position: "sticky", top: 0, zIndex: 1 }}>
                                <th style={{ width: 38, padding: "9px 8px", borderBottom: `1px solid ${COLORS.line}` }}>
                                    <input type="checkbox" checked={allCompletedSelected} onChange={toggleAllCompleted} title="Select completed jobs" />
                                </th>
                                {[
                                    "Job ID",
                                    "Source document",
                                    "Version",
                                    "Review date",
                                    "Duration",
                                    "AI credits",
                                    "Status",
                                    "Sections",
                                    "Findings",
                                    "Actions",
                                ].map((label) => (
                                    <th key={label} style={{ padding: "9px 8px", borderBottom: `1px solid ${COLORS.line}`, textAlign: "left", color: COLORS.soft, whiteSpace: "nowrap" }}>
                                        {label}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {jobs.map((job) => {
                                const style = statusStyle(job.status);
                                const selectable = job.status === "COMPLETED";
                                return (
                                    <tr key={job.job_id} style={{ borderBottom: `1px solid ${COLORS.line}` }}>
                                        <td style={{ padding: "8px", textAlign: "center" }}>
                                            <input
                                                type="checkbox"
                                                disabled={!selectable}
                                                checked={selected.has(job.job_id)}
                                                onChange={() => toggleSelected(job.job_id)}
                                            />
                                        </td>
                                        <td style={{ padding: "8px", fontFamily: COLORS.mono }}>
                                            <button
                                                onClick={() => onOpenJob(job.job_id, "findings")}
                                                style={{ border: "none", background: "transparent", color: COLORS.accent, cursor: "pointer", fontFamily: COLORS.mono, fontWeight: 700, padding: 0 }}
                                                title="Open Findings"
                                            >
                                                {job.job_id}
                                            </button>
                                        </td>
                                        <td style={{ padding: "8px", maxWidth: 360 }}>
                                            <div style={{ fontWeight: 650, marginBottom: 2 }}>{job.document_title || "-"}</div>
                                            <div style={{ color: COLORS.soft, wordBreak: "break-all" }}>{job.document_url || "-"}</div>
                                        </td>
                                        <td style={{ padding: "8px" }}>
                                            {job.source_version || <span style={{ color: COLORS.soft }}>Timestamp</span>}
                                            <div style={{ color: COLORS.soft, marginTop: 2 }}>
                                                {formatDate(job.source_version_timestamp)}
                                            </div>
                                        </td>
                                        <td style={{ padding: "8px", whiteSpace: "nowrap" }}>{formatDate(job.completed_at || job.updated_at || job.created_at)}</td>
                                        <td style={{ padding: "8px", whiteSpace: "nowrap" }}>{formatDuration(job.duration_seconds)}</td>
                                        <td style={{ padding: "8px", whiteSpace: "nowrap", fontFamily: COLORS.mono }}>{formatCredits(job.ai_credits)}</td>
                                        <td style={{ padding: "8px" }}>
                                            <span style={{ ...style, display: "inline-flex", padding: "3px 8px", borderRadius: 100, fontWeight: 700, whiteSpace: "nowrap" }}>
                                                {job.status === "RUNNING" ? "In Progress" : job.status === "QUEUED" ? "Pending" : String(job.status || "-").replaceAll("_", " ")}
                                            </span>
                                        </td>
                                        <td style={{ padding: "8px", whiteSpace: "nowrap" }}>
                                            {Number(job.eligible_section_count || 0).toLocaleString()} / {Number(job.selected_section_count || 0).toLocaleString()}
                                        </td>
                                        <td style={{ padding: "8px" }}>
                                            {Number(job.finding_count || 0)}
                                        </td>
                                        <td style={{ padding: "8px", whiteSpace: "nowrap" }}>
                                            <div style={{ display: "flex", gap: 6 }}>
                                                <button
                                                    onClick={() => onOpenJob(job.job_id, "findings")}
                                                    style={{ padding: "6px 8px", border: `1px solid ${COLORS.line}`, borderRadius: 5, background: COLORS.panel, color: COLORS.accent, fontWeight: 650, cursor: "pointer" }}
                                                >
                                                    Findings
                                                </button>
                                                <button
                                                    onClick={() => onOpenJob(job.job_id, "telemetry")}
                                                    style={{ padding: "6px 8px", border: `1px solid ${COLORS.line}`, borderRadius: 5, background: COLORS.panel, color: COLORS.accent, fontWeight: 650, cursor: "pointer" }}
                                                >
                                                    Telemetry
                                                </button>
                                                {job.status !== "RUNNING" && job.status !== "QUEUED" && job.status !== "CANCEL_REQUESTED" && (
                                                    <button
                                                        onClick={() => removeJob(job)}
                                                        style={{ padding: "6px 8px", border: `1px solid ${COLORS.line}`, borderRadius: 5, background: COLORS.panel, color: COLORS.issue, fontWeight: 650, cursor: "pointer" }}
                                                    >
                                                        Delete
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                            {!jobs.length && (
                                <tr>
                                    <td colSpan={11} style={{ padding: 40, textAlign: "center", color: COLORS.soft }}>
                                        {loading ? "Loading review jobs..." : "No review jobs found."}
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    );
}
