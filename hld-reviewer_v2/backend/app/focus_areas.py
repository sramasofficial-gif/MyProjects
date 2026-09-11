"""
Focus areas are what the reviewer actually picks per section in the UI
(Requirement-3: "vulnerability, missing sections, security, etc.").
Each maps to one or more of the underlying checklist criteria already
defined in checklist.py, plus a sensible default model tier so the
model-assignment step in the UI starts pre-filled.
"""

FOCUS_AREAS = {
    "vulnerability_security": {
        "label": "Vulnerability & Security",
        "description": "PCI-DSS scope, authentication/lockout logic, data exposure paths.",
        "criteria": ["pci_dss", "dtmf_auth"],
        "default_model": "strong_model",
    },
    "missing_sections": {
        "label": "Missing Sections",
        "description": "Expected HLD sections that are absent, stubbed, or empty.",
        "criteria": ["completeness"],
        "default_model": "cheap_model",
    },
    "consistency": {
        "label": "Consistency",
        "description": "Terminology and component naming consistency across the document.",
        "criteria": ["consistency"],
        "default_model": "cheap_model",
    },
    "contact_flow_correctness": {
        "label": "Contact Flow Correctness",
        "description": "Branch termination, error/escalation paths in call/contact flows.",
        "criteria": ["contact_flow_correctness"],
        "default_model": "strong_model",
    },
    "integration_reliability": {
        "label": "Integration Reliability",
        "description": "Lambda/external service timeout, retry, and fallback behavior.",
        "criteria": ["lambda_integration"],
        "default_model": "cheap_model",
    },
    "nfr_coverage": {
        "label": "NFR Coverage",
        "description": "Concrete latency, concurrency, throughput, and availability targets.",
        "criteria": ["nfr"],
        "default_model": "cheap_model",
    },
    "resilience": {
        "label": "Resilience & DR",
        "description": "Disaster recovery, failover, rollback, RTO/RPO definition.",
        "criteria": ["resilience"],
        "default_model": "strong_model",
    },
    "error_handling": {
        "label": "Error Handling",
        "description": "Exception paths defined for every external dependency.",
        "criteria": ["error_handling"],
        "default_model": "cheap_model",
    },
}


def suggested_focus_areas(section_type: str) -> list[str]:
    """Pre-check the focus areas most relevant to a section's detected type."""
    mapping = {
        "architecture_overview": ["missing_sections", "consistency"],
        "contact_flow_design": ["contact_flow_correctness", "vulnerability_security"],
        "integrations": ["integration_reliability", "error_handling"],
        "security": ["vulnerability_security"],
        "nfr": ["nfr_coverage"],
        "resilience": ["resilience"],
        "data_flow": ["contact_flow_correctness", "vulnerability_security"],
        "error_handling": ["error_handling"],
        "unclassified": ["missing_sections"],
    }
    return mapping.get(section_type, ["missing_sections"])
