"""Checklist definitions used to build the Stage 2 structured-review prompt."""

from .focus_config import FOCUS_AREAS

CHECKLIST_DEFINITIONS = {
    "completeness": "Are all expected HLD sections present and non-empty (scope, architecture, "
    "assumptions, dependencies)? Flag anything missing or stubbed out.",
    "consistency": "Is terminology consistent with the rest of the document (e.g. same names "
    "for the same components/flows)? Flag contradictions.",
    "contact_flow_correctness": "For contact flow / call flow descriptions: are all branches "
    "terminated (success, failure, timeout, no-input)? Is there an explicit error/escalation path?",
    "dtmf_auth": "For DTMF and authentication steps: is the number of retry attempts bounded? "
    "Is there a defined lockout/escalation-to-agent behavior after max retries?",
    "lambda_integration": "For Lambda / external service integration points: is a timeout "
    "specified? Is retry behavior defined? Is there a fallback path if the call fails?",
    "pci_dss": "For anything touching cardholder data: is DTMF masking/redaction mentioned? "
    "Is the PCI-DSS scope boundary explicit (what is in scope vs. out of scope)?",
    "nfr": "Are non-functional requirements (latency, concurrency, throughput, availability "
    "targets) stated with concrete numbers, not vague language?",
    "resilience": "Is a disaster-recovery / failover / rollback plan described? Is a specific "
    "RTO/RPO or fallback IVR message mentioned?",
    "error_handling": "Are error and exception paths described for every external dependency "
    "mentioned in this section?",
}

SEVERITY_GUIDE = (
    "Use severity: 'high' (would cause an outage, security gap, or compliance failure), "
    "'medium' (would cause a poor caller experience or maintenance issue), "
    "'low' (style/clarity nit)."
)


def build_checklist_prompt(section_heading: str, section_text: str, checklist_keys: list[str]) -> str:
    checklist_lines = "\n".join(
        f"- {key}: {CHECKLIST_DEFINITIONS[key]}" for key in checklist_keys if key in CHECKLIST_DEFINITIONS
    )
    return f"""You are reviewing one section of a High-Level Design (HLD) document for an \
Amazon Connect IVR system in a credit-card banking context.

Section heading: "{section_heading}"

Section text:
---
{section_text}
---

Check this section against the following criteria:
{checklist_lines}

{SEVERITY_GUIDE}

Respond with ONLY a JSON array (no prose, no markdown fences). Each element:
{{"criterion": "<checklist key>", "finding": "<specific, actionable finding>", \
"severity": "high|medium|low", "needs_deep_review": true|false}}

If a criterion is fully satisfied, omit it from the array. If the section is empty or \
irrelevant to a criterion, omit that criterion. Set "needs_deep_review": true only for \
findings that require reasoning about caller-experience edge cases or security logic \
that a checklist pass can't fully verify (this triggers escalation to a stronger model).
If there are no findings at all, respond with an empty array: []
"""


def build_selected_focus_prompt(section_heading: str, section_text: str, focus_keys: list[str]) -> str:
    """
    Requirement-3 workflow: builds a review prompt for whichever focus areas the
    user selected for this section and assigned to the SAME model — one call
    covers every focus area routed to that model, rather than one call each.
    """
    focus_lines = "\n".join(
        f"- {key} ({FOCUS_AREAS[key]['label']}): {FOCUS_AREAS[key]['description']}"
        for key in focus_keys
        if key in FOCUS_AREAS
    )
    any_escalatable = any(FOCUS_AREAS.get(k, {}).get("escalate") for k in focus_keys)
    escalate_instruction = (
        "For focus areas that involve security/vulnerability reasoning, set "
        '"needs_deep_review": true only when you are genuinely uncertain whether something '
        "is exploitable and a second reasoning pass would help — not for every finding."
        if any_escalatable
        else 'Always set "needs_deep_review": false for this section.'
    )

    return f"""You are reviewing one section of a High-Level Design (HLD) document for an \
Amazon Connect IVR system in a credit-card banking context.

Section heading: "{section_heading}"

Section text:
---
{section_text}
---

Review this section against the following user-selected focus areas ONLY:
{focus_lines}

{SEVERITY_GUIDE}
{escalate_instruction}

Respond with ONLY a JSON array (no prose, no markdown fences). Each element:
{{"focus_area": "<one of the focus area keys above>", "finding": "<specific, actionable finding>", \
"severity": "high|medium|low", "needs_deep_review": true|false}}

Omit any focus area that is fully satisfied for this section. If there are no findings at \
all, respond with an empty array: []
"""


def build_selected_deep_review_prompt(section_heading: str, section_text: str, prior_findings: list[dict]) -> str:
    findings_text = "\n".join(f"- [{f['severity']}] {f['focus_area']}: {f['finding']}" for f in prior_findings)
    return f"""You are doing a deeper reasoning-level review of one HLD section, focused on \
items an initial pass flagged as uncertain. Amazon Connect IVR, credit-card banking context.

Section heading: "{section_heading}"

Section text:
---
{section_text}
---

Items flagged for deeper review:
{findings_text}

For each, reason step by step about whether it's a real, exploitable gap. Respond with ONLY \
a JSON array, same schema as before but with "needs_deep_review" omitted and a "reasoning" \
field added:
{{"focus_area": "...", "finding": "...", "severity": "high|medium|low", "reasoning": "..."}}
"""


def build_deep_review_prompt(section_heading: str, section_text: str, prior_findings: list[dict]) -> str:
    findings_text = "\n".join(f"- [{f['severity']}] {f['criterion']}: {f['finding']}" for f in prior_findings)
    return f"""You are doing a deeper reasoning-level review of one HLD section that was \
flagged by an initial checklist pass. Amazon Connect IVR, credit-card banking context.

Section heading: "{section_heading}"

Section text:
---
{section_text}
---

Initial checklist flagged these items for deeper review:
{findings_text}

For each flagged item, reason step by step about whether it represents a real gap \
(e.g. could a caller bypass authentication, could a race condition drop a call, could \
cardholder data leak through a non-obvious path). Respond with ONLY a JSON array, same \
schema as before but with "needs_deep_review" omitted and a "reasoning" field added:
{{"criterion": "...", "finding": "...", "severity": "high|medium|low", "reasoning": "..."}}
"""
