import process from "node:process";
import readline from "node:readline";
import fs from "node:fs";
import path from "node:path";
import { CopilotClient, RuntimeConnection } from "@github/copilot-sdk";

/**
 * HLD Review Copilot Daemon
 *
 * Input: one JSON request per stdin line.
 * Output: one JSON response per stdout line.
 *
 * The daemon supports:
 *   - multi-scope HLD review in one turn per section
 *   - text/table/diagram/image evidence
 *   - actual image attachments to Copilot sessions
 *   - structured findings rather than section summaries
 *
 * The Python server passes visualEvidence as absolute file paths when the
 * selected review scope requires visual inspection.
 */

const REVIEW_SCOPE_RULES = {
    functional: {
        label: "Functional Completeness",
        objective: "Check whether documented requirements, business rules, use cases, workflows, and expected behavior are complete and internally consistent.",
        categories: ["Requirements", "Business Rule", "Workflow", "Use Case", "Completeness"]
    },
    architecture: {
        label: "Architecture",
        objective: "Assess architectural structure, component responsibilities, boundaries, dependencies, data flow, deployment topology, and consistency between text, tables, and visuals.",
        categories: ["Architecture", "Component Boundary", "Data Flow", "Dependency", "Design Consistency", "Single Point of Failure"]
    },
    security: {
        label: "Security",
        objective: "Assess authentication, authorization, IAM, encryption, secrets, network boundaries, access controls, data protection, and security architecture controls.",
        categories: ["Authentication", "Authorization", "IAM", "Encryption", "Secrets", "Network Security", "Data Protection"]
    },
    vulnerability: {
        label: "Vulnerability",
        objective: "Identify evidence-supported security weaknesses and attack surfaces such as injection, exposed interfaces, weak access control, unsafe trust boundaries, or exploitable configuration gaps.",
        categories: ["Attack Surface", "Input Validation", "Access Control", "Injection", "Trust Boundary", "Configuration Weakness"]
    },
    performance: {
        label: "Performance",
        objective: "Assess latency, throughput, capacity, concurrency, response time, scaling assumptions, and performance-related design constraints.",
        categories: ["Latency", "Throughput", "Capacity", "Concurrency", "Scalability", "Response Time"]
    },
    reliability: {
        label: "Reliability & Availability",
        objective: "Assess failure handling, retries, timeouts, redundancy, recovery, backups, failover, resilience, and availability assumptions.",
        categories: ["Failover", "Retry", "Timeout", "Recovery", "Redundancy", "Availability", "Resilience"]
    },
    integration: {
        label: "Integration",
        objective: "Assess APIs, events, queues, Lambda integrations, service interfaces, payload contracts, external dependencies, and integration error handling.",
        categories: ["API", "Event", "Interface", "Payload", "External Dependency", "Integration Error Handling"]
    },
    compliance: {
        label: "Compliance",
        objective: "Assess explicitly documented regulatory, policy, retention, audit, and control requirements without assuming a regulation that is not evidenced in the HLD.",
        categories: ["PCI", "GDPR", "HIPAA", "Retention", "Audit", "Policy", "Regulatory Control"]
    },
    documentation: {
        label: "Documentation Quality",
        objective: "Assess completeness, clarity, consistency, terminology, traceability, unresolved placeholders, and consistency between documented artifacts.",
        categories: ["Completeness", "Clarity", "Terminology", "Traceability", "Consistency", "Missing Detail"]
    },
    testability: {
        label: "Testability",
        objective: "Assess whether the design provides sufficient observable behavior, validation criteria, error paths, test conditions, and automation opportunities.",
        categories: ["Testability", "Validation", "Acceptance Criteria", "Error Path", "Automation"]
    },
    cost: {
        label: "Cost Optimization",
        objective: "Assess resource sizing, consumption assumptions, licensing, service selection, and opportunities for cost-aware design choices when supported by the HLD.",
        categories: ["Sizing", "Consumption", "Licensing", "Resource Utilization", "Cost Assumption"]
    },
    ivr: {
        label: "IVR / Contact Center",
        objective: "Assess Amazon Connect and IVR flows, prompts, queues, caller experience, Lambda/Lex integration, transfer behavior, retries, and disconnect/error handling.",
        categories: ["Contact Flow", "Prompt", "Queue", "Lambda", "Lex", "Transfer", "Retry", "Disconnect", "Caller Experience"]
    }
};

const VISUAL_SCOPES = new Set([
    "architecture",
    "security",
    "vulnerability",
    "integration",
    "ivr",
    "documentation",
    "reliability",
    "performance"
]);

function normalizeScopes(scopes) {
    const input = Array.isArray(scopes) ? scopes : [];
    const normalized = input
        .map((scope) => String(scope || "").trim().toLowerCase())
        .filter((scope) => REVIEW_SCOPE_RULES[scope]);

    return [...new Set(normalized)];
}

function normalizeResponseText(response) {
    let rawText = "";

    if (typeof response === "string") rawText = response;
    else if (response?.data?.content) rawText = response.data.content;
    else if (response?.content) rawText = response.content;
    else if (response?.message?.content) rawText = response.message.content;

    return (rawText || "")
        .trim()
        .replace(/^```(?:json)?\s*/i, "")
        .replace(/\s*```$/i, "")
        .trim();
}

function buildScopeInstruction(scopes) {
    if (!scopes.length) {
        return `
Review the HLD section from a general enterprise architecture perspective. Identify only evidence-supported findings and do not invent requirements.
`.trim();
    }

    return scopes.map((scope) => {
        const rule = REVIEW_SCOPE_RULES[scope];
        return `- ${rule.label}: ${rule.objective} Relevant finding categories include: ${rule.categories.join(", ")}.`;
    }).join("\n");
}

function buildStructuredReviewPrompt(request, scopes, attachments) {
    const scopeLabels = scopes.length
        ? scopes.map((scope) => REVIEW_SCOPE_RULES[scope]?.label || scope).join(", ")
        : "General HLD Review";

    const visualInstruction = attachments.length > 0
        ? `
VISUAL EVIDENCE:
The attached file(s) are actual rendered visual evidence for this HLD section.
Inspect the images themselves. Review visible components, labels, arrows, connectors, trust/security boundaries, groupings, topology, and relationships.
Use visual observations as evidence when they materially support a finding.
Do not claim that a visual was reviewed unless an attachment was actually provided.
`
        : `
VISUAL EVIDENCE:
No visual attachment is available for this request. Do not claim that you inspected an image or diagram.
If the text indicates that a diagram/image exists but no visual attachment was provided, mark the relevant item as manual review when visual inspection is necessary.
`;

    return `
You are an expert Enterprise HLD Review Analyst.

You are reviewing ONE HLD section from a corporate High-Level Design document.
Selected review scopes: ${scopeLabels}

Review objectives by selected scope:
${buildScopeInstruction(scopes)}

SECTION REFERENCE:
${request.relativePath}

CONTENT TYPES:
${JSON.stringify(request.contentTypes || [])}

RAW HLD SECTION CONTENT:
${request.source || "(no text content supplied)"}
${visualInstruction}

IMPORTANT REVIEW PRINCIPLES:
1. A summary is NOT a finding. A finding must identify a specific issue, gap, inconsistency, ambiguity, risk, or missing control supported by evidence.
2. Do not convert every section description into a problem. If no issue is evidenced, return a PASS check instead.
3. Do not invent requirements, architecture components, controls, regulations, or system behavior not supported by the supplied HLD evidence.
4. Separate facts/evidence from the analytical conclusion.
5. If text, table, and visual evidence disagree, treat that inconsistency as a finding and cite the conflicting evidence.
6. Use MANUAL_REVIEW when a conclusion requires an artifact or validation that is not available in the supplied evidence.
7. Severity must reflect the potential consequence and evidence strength. Use only: Critical, High, Medium, Low, Informational.
8. Confidence must be a number from 0 to 1.
9. Produce findings only for the selected scopes.

RETURN EXACTLY THIS JSON SHAPE:
{
  "document_metadata": {
    "title": ${JSON.stringify(request.relativePath)},
    "review_scopes": ${JSON.stringify(scopes)},
    "content_types": ${JSON.stringify(request.contentTypes || [])},
    "visual_reviewed": ${attachments.length > 0}
  },
  "review_summary": {
    "overall_status": "PASS|FINDINGS|MANUAL_REVIEW",
    "finding_count": 0,
    "pass_count": 0,
    "manual_review_count": 0
  },
  "findings": [
    {
      "finding_id": "F-001",
      "scope": "architecture",
      "category": "Data Flow",
      "severity": "Medium",
      "title": "Short actionable finding title",
      "finding": "Specific issue or control gap identified from the evidence",
      "evidence": {
        "text": "Relevant evidence from the supplied HLD text",
        "visual_observation": "Relevant observation from the attached image, or empty string when not applicable"
      },
      "impact": "Why this matters to the solution",
      "recommendation": "Concrete action to address the finding",
      "confidence": 0.85,
      "section_reference": ${JSON.stringify(request.relativePath)},
      "content_types": ${JSON.stringify(request.contentTypes || [])},
      "visual_reviewed": ${attachments.length > 0}
    }
  ],
  "passed_checks": [
    {
      "scope": "architecture",
      "category": "Component Boundary",
      "check": "What was checked",
      "evidence": "Evidence supporting the pass",
      "section_reference": ${JSON.stringify(request.relativePath)},
      "visual_reviewed": ${attachments.length > 0}
    }
  ],
  "manual_review": [
    {
      "scope": "architecture",
      "reason": "What could not be conclusively validated from the supplied evidence",
      "required_action": "What a human reviewer should validate",
      "section_reference": ${JSON.stringify(request.relativePath)}
    }
  ],
  "ivr_flow_requirements": []
}

STRICT OUTPUT RULES:
- Output valid JSON only.
- No markdown fences.
- No commentary before or after the JSON.
- findings[] must contain only actual review findings, not summaries.
- passed_checks[] contains positive validations that were actually supported by evidence.
- manual_review[] contains unresolved items requiring human or external validation.
- Keep evidence concise and grounded in the supplied section.
`.trim();
}

function collectAttachments(request) {
    const attachments = [];
    if (!request.visualReviewRequired || !Array.isArray(request.visualEvidence)) {
        return attachments;
    }

    for (const evidence of request.visualEvidence) {
        const evidencePath = typeof evidence === "string"
            ? evidence
            : evidence?.path;

        if (!evidencePath || !path.isAbsolute(evidencePath)) {
            process.stderr.write(
                `[VISUAL REVIEW] Ignoring non-absolute visual evidence path: ${String(evidencePath)}\n`
            );
            continue;
        }

        if (!fs.existsSync(evidencePath)) {
            process.stderr.write(
                `[VISUAL REVIEW] Visual evidence file not found: ${evidencePath}\n`
            );
            continue;
        }

        attachments.push({
            type: "file",
            path: evidencePath,
            displayName: evidence?.displayName || path.basename(evidencePath)
        });
    }

    return attachments;
}

function ensureStructuredReview(parsed, request, scopes, visualReviewed) {
    const result = parsed && typeof parsed === "object" ? parsed : {};

    result.document_metadata = result.document_metadata || {};
    result.document_metadata.title = result.document_metadata.title || request.relativePath;
    result.document_metadata.review_scopes = scopes;
    result.document_metadata.content_types = request.contentTypes || [];
    result.document_metadata.visual_reviewed = Boolean(visualReviewed);

    result.review_summary = result.review_summary || {};
    result.findings = Array.isArray(result.findings) ? result.findings : [];
    result.passed_checks = Array.isArray(result.passed_checks) ? result.passed_checks : [];
    result.manual_review = Array.isArray(result.manual_review) ? result.manual_review : [];
    result.ivr_flow_requirements = Array.isArray(result.ivr_flow_requirements)
        ? result.ivr_flow_requirements
        : [];

    // Defensive normalization: never allow a model to claim visual review when
    // the SDK request had no actual visual attachment.
    for (const finding of result.findings) {
        finding.visual_reviewed = Boolean(visualReviewed && finding.visual_reviewed);
        finding.section_reference = finding.section_reference || request.relativePath;
        finding.content_types = finding.content_types || request.contentTypes || [];
    }

    for (const check of result.passed_checks) {
        check.visual_reviewed = Boolean(visualReviewed && check.visual_reviewed);
        check.section_reference = check.section_reference || request.relativePath;
    }

    result.review_summary.finding_count = result.findings.length;
    result.review_summary.pass_count = result.passed_checks.length;
    result.review_summary.manual_review_count = result.manual_review.length;

    if (result.findings.length > 0) {
        result.review_summary.overall_status = "FINDINGS";
    } else if (result.manual_review.length > 0) {
        result.review_summary.overall_status = "MANUAL_REVIEW";
    } else {
        result.review_summary.overall_status = "PASS";
    }

    return result;
}

async function safeGetSessionMetrics(session) {
    try {
        if (!session?.rpc?.usage?.getMetrics) {
            return null;
        }
        const metrics = await session.rpc.usage.getMetrics();
        return metrics || null;
    } catch (error) {
        process.stderr.write(
            `[COPILOT USAGE] session.rpc.usage.getMetrics unavailable: ${String(error)}\n`
        );
        return null;
    }
}

async function safeGetContextInfo(session) {
    try {
        if (!session?.rpc?.metadata?.contextInfo) {
            return null;
        }
        const result = await session.rpc.metadata.contextInfo({
            promptTokenLimit: 0,
            outputTokenLimit: 0,
        });
        return result?.contextInfo || null;
    } catch (error) {
        process.stderr.write(
            `[COPILOT CONTEXT] session.rpc.metadata.contextInfo unavailable: ${String(error)}\n`
        );
        return null;
    }
}

function waitForSessionIdle(session, timeoutMs) {
    return new Promise((resolve, reject) => {
        let settled = false;
        const timer = setTimeout(() => {
            if (settled) return;
            settled = true;
            reject(new Error(`Timeout after ${timeoutMs}ms waiting for session.idle`));
        }, timeoutMs);

        const done = () => {
            if (settled) return;
            settled = true;
            clearTimeout(timer);
            resolve();
        };

        session.on("session.idle", done);
    });
}

function normalizeUsageRecord(data) {
    return {
        model: data?.model || null,
        inputTokens: Number(data?.inputTokens || 0),
        outputTokens: Number(data?.outputTokens || 0),
        reasoningTokens: Number(data?.reasoningTokens || 0),
        cacheReadTokens: Number(data?.cacheReadTokens || 0),
        cacheWriteTokens: Number(data?.cacheWriteTokens || 0),
        costMultiplier: Number(data?.cost || 0),
        durationMs: Number(data?.duration || 0),
        timeToFirstTokenMs: Number(data?.timeToFirstTokenMs || 0),
        interTokenLatencyMs: Number(data?.interTokenLatencyMs || 0),
        reasoningEffort: data?.reasoningEffort || null,
        initiator: data?.initiator || null,
        apiCallId: data?.apiCallId || null,
        serviceRequestId: data?.serviceRequestId || null,
        apiEndpoint: data?.apiEndpoint || null,
        providerCallId: data?.providerCallId || null,
        finishReason: data?.finishReason || null,
        contentFilterTriggered: Boolean(data?.contentFilterTriggered),
        copilotUsage: data?.copilotUsage || null,
    };
}

function normalizeSessionMetrics(metrics) {
    if (!metrics || typeof metrics !== 'object') return null;

    const modelMetrics = {};
    for (const [model, metric] of Object.entries(metrics.modelMetrics || {})) {
        if (!metric) continue;
        modelMetrics[model] = {
            inputTokens: Number(metric?.usage?.inputTokens || 0),
            outputTokens: Number(metric?.usage?.outputTokens || 0),
            reasoningTokens: Number(metric?.usage?.reasoningTokens || 0),
            totalNanoAiu: Number(metric?.totalNanoAiu || 0),
        };
    }

    const totalNanoAiu = Number(metrics.totalNanoAiu || 0);

    return {
        totalNanoAiu,
        aiCreditsFromNanoAiu: totalNanoAiu / 1e9,
        totalPremiumRequestCost: Number(metrics.totalPremiumRequestCost || 0),
        modelMetrics,
        tokenDetails: metrics.tokenDetails || {},
    };
}

function buildUsageSummary({ request, scopes, usageEvents, sessionMetrics, contextInfo, visualReviewed, turnStatus }) {
    const eventInput = usageEvents.reduce((sum, item) => sum + item.inputTokens, 0);
    const eventOutput = usageEvents.reduce((sum, item) => sum + item.outputTokens, 0);
    const eventReasoning = usageEvents.reduce((sum, item) => sum + item.reasoningTokens, 0);
    const eventCacheRead = usageEvents.reduce((sum, item) => sum + item.cacheReadTokens, 0);
    const eventCacheWrite = usageEvents.reduce((sum, item) => sum + item.cacheWriteTokens, 0);
    const eventDuration = usageEvents.reduce((sum, item) => sum + item.durationMs, 0);

    const modelMetrics = sessionMetrics?.modelMetrics || {};
    const sessionInput = Object.values(modelMetrics).reduce((sum, item) => sum + item.inputTokens, 0);
    const sessionOutput = Object.values(modelMetrics).reduce((sum, item) => sum + item.outputTokens, 0);

    // Reasoning-token counts are taken from assistant.usage events because the
    // session modelMetrics schema currently documents input/output and AIU cost,
    // while assistant.usage explicitly exposes reasoningTokens.
    const models = sessionMetrics
        ? Object.keys(modelMetrics)
        : [...new Set(usageEvents.map((item) => item.model).filter(Boolean))];

    const modelBreakdown = {};
    for (const model of models) {
        const metric = modelMetrics[model];
        const eventRows = usageEvents.filter((item) => item.model === model);
        modelBreakdown[model] = {
            calls: eventRows.length,
            inputTokens: metric ? metric.inputTokens : eventRows.reduce((sum, item) => sum + item.inputTokens, 0),
            outputTokens: metric ? metric.outputTokens : eventRows.reduce((sum, item) => sum + item.outputTokens, 0),
            reasoningTokens: eventRows.reduce((sum, item) => sum + item.reasoningTokens, 0),
            totalNanoAiu: metric ? metric.totalNanoAiu : 0,
            aiCreditsFromNanoAiu: metric ? metric.totalNanoAiu / 1e9 : 0,
        };
    }

    const inputTokens = sessionMetrics ? sessionInput : eventInput;
    const outputTokens = sessionMetrics ? sessionOutput : eventOutput;
    const reasoningTokens = eventReasoning;
    const totalNanoAiu = sessionMetrics?.totalNanoAiu || 0;
    const premiumRequestCost = sessionMetrics?.totalPremiumRequestCost || 0;

    const normalizedContextInfo = contextInfo ? {
        totalTokens: Number(contextInfo.totalTokens || 0),
        promptTokenLimit: Number(contextInfo.promptTokenLimit || 0),
        systemTokens: Number(contextInfo.systemTokens || 0),
        conversationTokens: Number(contextInfo.conversationTokens || 0),
        toolDefinitionsTokens: Number(contextInfo.toolDefinitionsTokens || 0),
    } : null;

    return {
        sectionId: Number(request.sectionId || 0),
        sectionHeading: request.sectionHeading || request.relativePath || "",
        reviewScopes: scopes,
        attributionMode: "shared-section-call",
        visualReviewed: Boolean(visualReviewed),
        modelCalls: usageEvents.length,
        models,
        inputTokens,
        outputTokens,
        totalTokens: inputTokens + outputTokens,
        reasoningTokens,
        cacheReadTokens: eventCacheRead,
        cacheWriteTokens: eventCacheWrite,
        durationMs: eventDuration,
        totalNanoAiu,
        aiCreditsFromNanoAiu: totalNanoAiu / 1e9,
        premiumRequestCost,
        usageComplete: usageEvents.length > 0,
        turnStatus: turnStatus || "completed",
        usageSource: sessionMetrics ? "session.rpc.usage.getMetrics + assistant.usage" : "assistant.usage events",
        contextInfo: normalizedContextInfo,
        modelBreakdown,
        apiCalls: usageEvents,
    };
}

async function runOneReviewRequest(client, request, scopes, attachments) {
    let session = null;
    const usageEvents = [];
    let assistantMessages = [];
    let contextInfo = null;
    let turnStatus = "started";
    const WAIT_TIMEOUT_MS = 180000;

    try {
        session = await client.createSession({
            streaming: true,
            systemMessage: {
                content: `
You are an expert Enterprise Systems Analyst conducting evidence-based High-Level Design reviews.
Your outputs must distinguish review findings from summaries.
Only report defects, risks, gaps, inconsistencies, missing controls, ambiguities, or unresolved validation needs that are supported by supplied evidence.
Never invent requirements or claim to have inspected a visual artifact unless an image attachment is actually supplied.
Return machine-readable JSON when the caller requests JSON.
`.trim()
            }
        });

        session.on("assistant.message", (event) => {
            const content = event?.data?.content;
            if (typeof content === "string" && content.trim()) {
                assistantMessages.push(content.trim());
            }
        });

        session.on("session.usage_info", (event) => {
            const data = event?.data || {};
            process.stderr.write(
                `[COPILOT CONTEXT] section=${request.sectionId || "?"} ` +
                `current=${Number(data.currentTokens || 0)} limit=${Number(data.tokenLimit || 0)}\n`
            );
        });

        session.on("assistant.usage", (event) => {
            const record = normalizeUsageRecord(event?.data || {});
            usageEvents.push(record);
            process.stderr.write(
                `[COPILOT USAGE] section=${request.sectionId || "?"} scopes=${scopes.join(",")} ` +
                `model=${record.model || "unknown"} input=${record.inputTokens} ` +
                `output=${record.outputTokens} reasoning=${record.reasoningTokens} ` +
                `costMultiplier=${record.costMultiplier}\n`
            );
        });

        const specificPrompt = request.diagramType === "HLD_SEGMENTATION_MODE"
            ? buildStructuredReviewPrompt(
                {
                    ...request,
                    contentTypes: Array.isArray(request.contentTypes) ? request.contentTypes : []
                },
                scopes,
                attachments
            )
            : `
Analyze ${request.relativePath} and produce a professional Mermaid diagram from the source code.
Output raw Mermaid syntax only.
`.trim();

        if (attachments.length > 0) {
            process.stderr.write(
                `[VISUAL REVIEW] Attaching ${attachments.length} image(s) for ${request.relativePath} scopes=${scopes.join(",")}\n`
            );
            for (const attachment of attachments) {
                process.stderr.write(
                    `[VISUAL REVIEW]   -> ${attachment.displayName}: ${attachment.path}\n`
                );
            }
        }

        // Use send() + an explicit session.idle wait rather than sendAndWait().
        // GitHub documents a 60s default for sendAndWait; HLD visual review can
        // legitimately exceed that. The explicit wait below gives us 3 minutes
        // while still using the session's true idle event as the completion signal.
        const messageId = await session.send({
            prompt: specificPrompt,
            ...(attachments.length > 0 ? { attachments } : {})
        });

        process.stderr.write(
            `[COPILOT TURN] section=${request.sectionId || "?"} message=${messageId} ` +
            `waiting_for_idle=${WAIT_TIMEOUT_MS}ms\n`
        );

        try {
            await waitForSessionIdle(session, WAIT_TIMEOUT_MS);
            turnStatus = "completed";
        } catch (waitError) {
            turnStatus = "timeout";
            process.stderr.write(
                `[COPILOT TURN] section=${request.sectionId || "?"} wait timeout: ${String(waitError)}\n`
            );
            throw waitError;
        }

        contextInfo = await safeGetContextInfo(session);
        const sessionMetricsRaw = await safeGetSessionMetrics(session);
        const sessionMetrics = normalizeSessionMetrics(sessionMetricsRaw);

        if (contextInfo) {
            process.stderr.write(
                `[COPILOT CONTEXT] section=${request.sectionId || "?"} ` +
                `total=${contextInfo.totalTokens || 0} ` +
                `system=${contextInfo.systemTokens || 0} ` +
                `conversation=${contextInfo.conversationTokens || 0} ` +
                `tools=${contextInfo.toolDefinitionsTokens || 0} ` +
                `limit=${contextInfo.promptTokenLimit || 0}\n`
            );
        }

        const response = assistantMessages.length > 0
            ? { data: { content: assistantMessages[assistantMessages.length - 1] } }
            : undefined;
        const rawText = normalizeResponseText(response);

        if (request.diagramType !== "HLD_SEGMENTATION_MODE") {
            return {
                success: true,
                mermaid_string: rawText,
                usage: buildUsageSummary({
                    request,
                    scopes,
                    usageEvents,
                    sessionMetrics,
                    contextInfo,
                    turnStatus,
                    visualReviewed: attachments.length > 0
                })
            };
        }

        let parsed;
        try {
            parsed = JSON.parse(rawText);
        } catch (parseError) {
            process.stderr.write(
                `[HLD REVIEW] Invalid JSON returned for ${request.relativePath} scopes=${scopes.join(",")}: ${String(parseError)}\n`
            );
            return {
                success: false,
                error: "Copilot returned invalid JSON for the structured HLD review.",
                raw_response: rawText.slice(0, 2000),
                usage: buildUsageSummary({
                    request,
                    scopes,
                    usageEvents,
                    sessionMetrics,
                    contextInfo,
                    turnStatus,
                    visualReviewed: attachments.length > 0
                })
            };
        }

        const structuredReview = ensureStructuredReview(
            parsed,
            {
                ...request,
                contentTypes: Array.isArray(request.contentTypes) ? request.contentTypes : []
            },
            scopes,
            attachments.length > 0
        );

        return {
            success: true,
            mermaid_string: JSON.stringify(structuredReview),
            usage: buildUsageSummary({
                request,
                scopes,
                usageEvents,
                sessionMetrics,
                visualReviewed: attachments.length > 0
            })
        };
    } finally {
        if (session?.destroy) {
            await session.destroy().catch(() => {});
        }
    }
}

async function main() {
    let client = null;

    try {
        client = new CopilotClient({
            connection: RuntimeConnection.forStdio(),
            useLoggedInUser: true
        });
        await client.start();

        const rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout,
            terminal: false
        });

        for await (const line of rl) {
            if (!line.trim()) continue;

            try {
                const request = JSON.parse(line);
                const scopes = normalizeScopes(request.reviewScopes);
                const requestContentTypes = Array.isArray(request.contentTypes)
                    ? request.contentTypes
                    : [];
                const attachments = collectAttachments(request);
                const selectedScopes = scopes.length ? scopes : ["architecture"];
                const visualAllowed = selectedScopes.some((scope) => VISUAL_SCOPES.has(scope));
                const scopeAttachments = visualAllowed ? attachments : [];

                process.stderr.write(
                    `[HLD REVIEW] section=${request.sectionId || "?"} ` +
                    `scopes=${selectedScopes.join(",")} ` +
                    `visual=${scopeAttachments.length > 0}\n`
                );

                const result = await runOneReviewRequest(
                    client,
                    {
                        ...request,
                        contentTypes: requestContentTypes
                    },
                    selectedScopes,
                    scopeAttachments
                );

                if (request.diagramType !== "HLD_SEGMENTATION_MODE") {
                    process.stdout.write(JSON.stringify(result) + "\n");
                    continue;
                }

                if (!result.success) {
                    process.stdout.write(JSON.stringify(result) + "\n");
                    continue;
                }

                const chunkBlueprint = JSON.parse(result.mermaid_string);
                process.stdout.write(JSON.stringify({
                    success: true,
                    mermaid_string: JSON.stringify(chunkBlueprint),
                    usage: result.usage || null
                }) + "\n");
            } catch (innerError) {
                process.stdout.write(JSON.stringify({
                    success: false,
                    error: String(innerError)
                }) + "\n");
            }
        }
    } catch (globalError) {
        process.stderr.write(`Daemon Crash Exception: ${String(globalError)}\n`);
        process.exit(1);
    } finally {
        if (client?.stop) {
            await client.stop().catch(() => {});
        }
    }
}

await main();
