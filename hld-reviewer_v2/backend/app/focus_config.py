"""
Defines the selectable review focus areas and the models available to assign
to each one. This is the config surface for Requirement-3: the user picks
which sections to review, which focus areas apply per section, and which
model handles each focus area.
"""

# Focus areas the user can multi-select per section.
# `escalate` = True means findings from this focus area are eligible for a
# second reasoning pass (only if the first pass flags something uncertain),
# keeping spend on judgement calls, not blanket deep review.
FOCUS_AREAS = {
    "missing_sections": {
        "label": "Missing sections",
        "description": "Flags gaps against a standard HLD structure (scope, assumptions, "
        "dependencies, rollback) and stubbed-out or empty subsections.",
        "escalate": False,
        "default_model": "gpt-4o-mini",
    },
    "consistency": {
        "label": "Consistency",
        "description": "Terminology and naming consistency across the document; contradictions "
        "between sections.",
        "escalate": False,
        "default_model": "gpt-4o-mini",
    },
    "security": {
        "label": "Security / PCI-DSS",
        "description": "Authentication flows, DTMF masking, PCI-DSS scope boundaries, "
        "cardholder-data handling.",
        "escalate": True,
        "default_model": "gpt-4o",
    },
    "vulnerability": {
        "label": "Vulnerability analysis",
        "description": "Deeper reasoning about exploitable gaps: auth bypass, race conditions, "
        "privilege escalation paths, injection via IVR input.",
        "escalate": True,
        "default_model": "gpt-4o",
    },
    "contact_flow_correctness": {
        "label": "Contact flow correctness",
        "description": "Every branch (success, failure, timeout, no-input) terminates; "
        "escalation/error paths are explicit.",
        "escalate": False,
        "default_model": "gpt-4o-mini",
    },
    "nfr": {
        "label": "Non-functional requirements",
        "description": "Latency, concurrency, throughput and availability targets stated with "
        "concrete numbers.",
        "escalate": False,
        "default_model": "gpt-4o-mini",
    },
    "resilience": {
        "label": "Resilience / DR",
        "description": "Disaster recovery, failover, rollback plan, RTO/RPO or fallback IVR "
        "message.",
        "escalate": False,
        "default_model": "gpt-4o-mini",
    },
    "error_handling": {
        "label": "Error handling",
        "description": "Every external dependency has a described error/exception path.",
        "escalate": False,
        "default_model": "gpt-4o-mini",
    },
}

# Models sourced from GitHub Models (github.com/marketplace/models).
# Swap/extend freely — key must match what your GitHub Models endpoint expects.
AVAILABLE_MODELS = [
    {"key": "gpt-4o-mini", "label": "GPT-4o mini — fast, cheap, good for checklist-style checks"},
    {"key": "gpt-4o", "label": "GPT-4o — stronger reasoning, use for security/vulnerability"},
    {"key": "Meta-Llama-3.1-70B-Instruct", "label": "Llama 3.1 70B — open-weight alternative"},
]
