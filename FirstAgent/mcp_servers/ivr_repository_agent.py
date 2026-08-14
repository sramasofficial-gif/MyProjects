"""MCP server exposing services related to various file types supported in a IVR Contact Center Platform Project Repository.

The server communicates with VS Code over standard input/output.
Do not print normal application messages to stdout because stdout is
reserved for MCP protocol messages.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

# Allow execution as a script while still resolving the workspace package.
PROJECT_ROOT = (
    Path(__file__).parent.parent
    / "ivr_repo"
).resolve()
IVR_REPOSITORY_ROOT = PROJECT_ROOT

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

#from mcp.server.fastmcp import FastMCP
from mcp.server import MCPServer

#mcp = FastMCP("ivr_repo_svc")
mcp = MCPServer("ivr_repository_agent")

logger = logging.getLogger("repoProcessor")
logger.setLevel(logging.INFO)

LOG_FILE = Path(__file__).parent / "repo_processor.log"

file_handler = logging.FileHandler(LOG_FILE)

file_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s"
)

file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

logger.info("SERVER STARTED")

class ContactFlowAuditor:
    """
    Analyze structural complexity and dependencies in an
    Amazon Connect contact flow JSON file.
    """

    ERROR_SENSITIVE_BLOCK_TYPES = {
        "InvokeLambdaFunction",
        "Transfer",
        "TransferToFlow",
        "TransferToQueue",
        "GetCustomerInput",
        "GetParticipantInput",
    }

    def __init__(self, file_path: str | Path) -> None:
        self.file_path = Path(file_path).resolve()
        self.flow_data = self._load_flow()

    def _load_flow(self) -> dict[str, Any]:
        """
        Load and validate the Amazon Connect contact flow JSON file.
        """

        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Contact flow file was not found: {self.file_path}"
            )

        if not self.file_path.is_file():
            raise ValueError(
                f"Contact flow path is not a file: {self.file_path}"
            )

        if self.file_path.suffix.lower() != ".json":
            raise ValueError(
                "Contact flow auditor accepts only JSON files."
            )

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                flow_data = json.load(file)

        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid JSON in contact flow file. "
                f"Line {exc.lineno}, column {exc.colno}: {exc.msg}"
            ) from exc

        except OSError as exc:
            raise OSError(
                f"Unable to read contact flow file: {exc}"
            ) from exc

        if not isinstance(flow_data, dict):
            raise ValueError(
                "The contact flow JSON root must be a JSON object."
            )

        actions = flow_data.get("Actions")

        if actions is None:
            raise ValueError(
                "The JSON file does not contain an 'Actions' array."
            )

        if not isinstance(actions, list):
            raise ValueError(
                "The 'Actions' property must be a JSON array."
            )

        return flow_data

    @staticmethod
    def _extract_next_action(transition: Any) -> str | None:
        """
        Extract the target action ID from a transition.

        Amazon Connect transitions may be represented as:

        1. A string containing the target action ID.
        2. An object containing a NextAction property.
        """

        if isinstance(transition, str):
            transition = transition.strip()
            return transition if transition else None

        if isinstance(transition, dict):
            next_action = transition.get("NextAction")

            if isinstance(next_action, str):
                next_action = next_action.strip()
                return next_action if next_action else None

        return None

    def _get_outbound_paths(
        self,
        transitions: dict[str, Any],
    ) -> list[str]:
        """
        Extract every outbound target from an action's transitions.
        """

        outbound_paths: list[str] = []

        next_action = self._extract_next_action(
            transitions.get("NextAction")
        )

        if next_action:
            outbound_paths.append(next_action)

        errors = transitions.get("Errors", [])

        if isinstance(errors, list):
            for error_transition in errors:
                error_target = self._extract_next_action(
                    error_transition
                )

                if error_target:
                    outbound_paths.append(error_target)

        conditions = transitions.get("Conditions", [])

        if isinstance(conditions, list):
            for condition_transition in conditions:
                condition_target = self._extract_next_action(
                    condition_transition
                )

                if condition_target:
                    outbound_paths.append(condition_target)

        return outbound_paths

    def analyze(self) -> dict[str, Any]:
        """
        Calculate structural metrics for the contact flow.
        """

        blocks = self.flow_data.get("Actions", [])

        total_blocks = len(blocks)
        total_edges = 0
        decision_branches = 0
        lambda_count = 0
        unhandled_error_blocks = 0
        invalid_action_entries = 0

        lambda_action_ids: list[str] = []
        unhandled_error_action_ids: list[str] = []

        for block in blocks:
            if not isinstance(block, dict):
                invalid_action_entries += 1
                continue

            block_type = str(block.get("Type", ""))

            block_identifier = str(
                block.get("Identifier", "<unknown>")
            )

            transitions = block.get("Transitions", {})

            if not isinstance(transitions, dict):
                transitions = {}

            if (
                "Lambda" in block_type
                or block_type == "InvokeLambdaFunction"
            ):
                lambda_count += 1
                lambda_action_ids.append(block_identifier)

            outbound_paths = self._get_outbound_paths(transitions)

            edge_count = len(outbound_paths)
            total_edges += edge_count

            if edge_count > 1:
                decision_branches += edge_count - 1

            errors = transitions.get("Errors")

            if (
                block_type in self.ERROR_SENSITIVE_BLOCK_TYPES
                and isinstance(errors, list)
                and len(errors) == 0
            ):
                unhandled_error_blocks += 1
                unhandled_error_action_ids.append(block_identifier)

        if total_blocks > 0:
            mccabe_score = total_edges - total_blocks + 2
        else:
            mccabe_score = 1

        decision_score = decision_branches + 1

        return {
            "flow_name": self.flow_data.get(
                "Name",
                self.file_path.name,
            ),
            "file_name": self.file_path.name,
            "total_blocks": total_blocks,
            "total_edges": total_edges,
            "cyclomatic_complexity_mccabe": mccabe_score,
            "cyclomatic_complexity_decision": decision_score,
            "lambda_integrations": lambda_count,
            "lambda_action_ids": lambda_action_ids,
            "unhandled_error_blocks": unhandled_error_blocks,
            "unhandled_error_action_ids": (
                unhandled_error_action_ids
            ),
            "invalid_action_entries": invalid_action_entries,
        }

    @staticmethod
    def _get_complexity_status(score: int) -> dict[str, str]:
        """
        Return severity information for the McCabe score.
        """

        if score <= 10:
            return {
                "level": "pass",
                "label": "Low Risk",
                "message": (
                    "Complexity is within the preferred range."
                ),
            }

        if score <= 20:
            return {
                "level": "warning",
                "label": "Moderate Risk",
                "message": (
                    "Review the decision paths and consider "
                    "simplifying the contact flow."
                ),
            }

        return {
            "level": "fail",
            "label": "High Risk",
            "message": (
                "The contact flow should be considered for "
                "refactoring or decomposition."
            ),
        }

    @staticmethod
    def _get_block_status(
        total_blocks: int,
    ) -> dict[str, str]:
        """
        Return severity information for contact flow size.
        """

        if total_blocks <= 50:
            return {
                "level": "pass",
                "label": "Acceptable Size",
                "message": (
                    "The contact flow block count is acceptable."
                ),
            }

        if total_blocks <= 60:
            return {
                "level": "warning",
                "label": "Large Flow",
                "message": (
                    "The contact flow UI may be becoming difficult "
                    "to maintain."
                ),
            }

        return {
            "level": "fail",
            "label": "Oversized Flow",
            "message": (
                "Consider splitting the flow into smaller reusable "
                "contact flows or flow modules."
            ),
        }

    def generate_report(self) -> dict[str, Any]:
        """
        Generate a structured contact flow audit report.

        This method intentionally does not print to stdout and does
        not terminate the process.
        """

        metrics = self.analyze()

        complexity_score = metrics[
            "cyclomatic_complexity_mccabe"
        ]
        total_blocks = metrics["total_blocks"]

        complexity_status = self._get_complexity_status(
            complexity_score
        )
        block_status = self._get_block_status(total_blocks)

        audit_passed = (
            complexity_score <= 20
            and total_blocks <= 60
        )

        recommendations: list[str] = []

        if complexity_score > 20:
            recommendations.append(
                "Reduce decision branches or divide the flow into "
                "smaller reusable modules."
            )

        if total_blocks > 50:
            recommendations.append(
                "Review whether groups of actions can be moved into "
                "separate flows or Amazon Connect flow modules."
            )

        if metrics["unhandled_error_blocks"] > 0:
            recommendations.append(
                "Add explicit error transitions to the reported "
                "actions."
            )

        if metrics["lambda_integrations"] > 0:
            recommendations.append(
                "Verify timeout, failure, malformed response, and "
                "retry handling for the Lambda integrations."
            )

        if not recommendations:
            recommendations.append(
                "No threshold-based structural issues were found."
            )

        return {
            "success": True,
            "audit_passed": audit_passed,
            "metrics": metrics,
            "status": {
                "complexity": complexity_status,
                "flow_size": block_status,
            },
            "recommendations": recommendations,
        }

def resolve_repository_file(relative_path: str) -> Path:
    """
    Resolve a file path relative to ivr_repo.

    This prevents callers from accessing files outside the configured
    IVR repository.
    """

    if not isinstance(relative_path, str):
        raise ValueError("relative_path must be a string")

    relative_path = relative_path.strip()

    if not relative_path:
        raise ValueError("relative_path must not be empty")

    requested_path = Path(relative_path)

    if requested_path.is_absolute():
        raise ValueError(
            "Absolute paths are not allowed. Provide a path relative "
            "to the ivr_repo directory."
        )

    resolved_path = (
        IVR_REPOSITORY_ROOT / requested_path
    ).resolve()

    try:
        resolved_path.relative_to(IVR_REPOSITORY_ROOT)

    except ValueError as exc:
        raise ValueError(
            "The requested path is outside the IVR repository."
        ) from exc

    return resolved_path

@mcp.tool()
def find_files(extension: str = ".json") -> dict[str, object]:
    """
    Find repository files matching a pattern within IVR Contact Center Platform Project Repository.

    USE THIS TOOL WHEN:
    - User asks to locate files
    - User asks to find Terraform scripts
    - User asks to find Lambda source code
    - User asks to find Contact Flow JSON files

    Example prompts :
    'Find (or Locate or List) terraform scripts from IVR (Contact Center Platform) Project'
      -> pattern='*.tf'

    'Find (or Locate or List) Lambda files from IVR (Contact Center Platform) Project'
      -> pattern='*.ts'

    'Find (or Locate or List) contact flows from IVR (Contact Center Platform) Project'
      -> pattern='cf*.json'
    """

    if not extension.startswith("."):
        extension = "." + extension

    print("FIND_FILES CALLED", file=sys.stderr)
    logger.info(
        "find_files called with extension=%s",
        extension
    )

    #return [
    #    str(f.relative_to(PROJECT_ROOT))
    #    for f in PROJECT_ROOT.rglob(f"*{extension}")
    #    if f.is_file()
    #]
    return {
        "project_root": str(PROJECT_ROOT),
        "extension": extension,
        "files_found": [
            str(path.relative_to(PROJECT_ROOT))
            for path in PROJECT_ROOT.rglob(f"*{extension}")
            if path.is_file()
        ]
    } 


@mcp.tool()
def read_file(relative_path: str) -> str:
    """
    Read repository file.
    """

    path = (PROJECT_ROOT / relative_path).resolve()

    try:
        path.relative_to(PROJECT_ROOT)
    except ValueError:
        logger.error(
            "Outside repository: %s",
            relative_path
        )
        raise ValueError("Outside repository")

    return path.read_text(
        encoding="utf-8",
        errors="ignore"
    )


@mcp.tool()
def analyze_lambda(relative_path: str):
    """
    Analyze lambda source file.
    """

    content = read_file(relative_path)

    imports = []

    for line in content.splitlines():

        if line.startswith("import "):
            imports.append(line.strip())

        elif line.startswith("from "):
            imports.append(line.strip())

    return {
        "file": relative_path,
        "lines": len(content.splitlines()),
        "contains_handler":
            "lambda_handler" in content,
        "imports": imports
    }

@mcp.tool()
def audit_contact_flow(
    relative_path: str,
) -> dict[str, Any]:
    """
    Audit an Amazon Connect contact flow JSON file.

    Use this tool when the user asks to:

    - Audit an Amazon Connect contact flow
    - Calculate contact flow complexity
    - Calculate McCabe cyclomatic complexity
    - Count flow blocks and structural edges
    - Find Lambda integrations
    - Detect actions with potentially missing error handlers
    - Assess contact flow maintainability
    - Identify contact flows that may require refactoring

    The input must be a path relative to the configured ivr_repo
    directory.

    Example input:

        flows/cfAccountStatus.json

    Args:
        relative_path:
            Path of the Amazon Connect contact flow JSON file,
            relative to the ivr_repo directory.

    Returns:
        A structured dictionary containing audit metrics, audit
        status, diagnostics, and recommendations.
    """

    logger.info(
        "audit_contact_flow requested: relative_path=%s",
        relative_path,
    )

    try:
        flow_path = resolve_repository_file(relative_path)

        if not flow_path.exists():
            return {
                "success": False,
                "error": "file_not_found",
                "message": (
                    "Contact flow file was not found: "
                    f"{relative_path}"
                ),
                "relative_path": relative_path,
            }

        if not flow_path.is_file():
            return {
                "success": False,
                "error": "not_a_file",
                "message": (
                    "The requested path is not a file: "
                    f"{relative_path}"
                ),
                "relative_path": relative_path,
            }

        if flow_path.suffix.lower() != ".json":
            return {
                "success": False,
                "error": "unsupported_file_type",
                "message": (
                    "audit_contact_flow accepts only JSON files."
                ),
                "relative_path": relative_path,
            }

        auditor = ContactFlowAuditor(flow_path)
        report = auditor.generate_report()

        normalized_relative_path = flow_path.relative_to(
            IVR_REPOSITORY_ROOT
        ).as_posix()

        report["relative_path"] = normalized_relative_path

        logger.info(
            "audit_contact_flow completed: "
            "relative_path=%s, passed=%s, blocks=%s, "
            "edges=%s, complexity=%s",
            normalized_relative_path,
            report["audit_passed"],
            report["metrics"]["total_blocks"],
            report["metrics"]["total_edges"],
            report["metrics"][
                "cyclomatic_complexity_mccabe"
            ],
        )

        return report

    except FileNotFoundError as exc:
        logger.warning(
            "audit_contact_flow file not found: %s",
            exc,
        )

        return {
            "success": False,
            "error": "file_not_found",
            "message": str(exc),
            "relative_path": relative_path,
        }

    except ValueError as exc:
        logger.warning(
            "audit_contact_flow validation failed: "
            "relative_path=%s, error=%s",
            relative_path,
            exc,
        )

        return {
            "success": False,
            "error": "validation_error",
            "message": str(exc),
            "relative_path": relative_path,
        }

    except OSError as exc:
        logger.exception(
            "audit_contact_flow file access failed: "
            "relative_path=%s",
            relative_path,
        )

        return {
            "success": False,
            "error": "file_access_error",
            "message": str(exc),
            "relative_path": relative_path,
        }

    except Exception as exc:
        logger.exception(
            "Unexpected audit_contact_flow failure: "
            "relative_path=%s",
            relative_path,
        )

        return {
            "success": False,
            "error": "audit_failed",
            "message": str(exc),
            "relative_path": relative_path,
        }

@mcp.tool()
def audit_contact_flows(relative_paths: list):
    """
    Audit multiple Amazon Connect contact flows.

    Args:
        relative_paths:
            List of repository-relative JSON files.

    Returns:
        Structured JSON audit report.
    """

    summary = {
        "total_files": len(relative_paths),
        "successful_audits": 0,
        "failed_audits": 0,
        "total_blocks": 0,
        "total_edges": 0,
        "total_lambda_integrations": 0,
        "total_unhandled_error_blocks": 0,
        "high_risk_flows": []
    }

    flow_reports = []

    for relative_path in relative_paths:

        try:
            flow_path = resolve_repository_file(
                relative_path
            )

            auditor = ContactFlowAuditor(
                flow_path
            )

            report = auditor.generate_report()

            metrics = report["metrics"]

            blocks = metrics["total_blocks"]

            complexity = metrics[
                "cyclomatic_complexity_mccabe"
            ]

            #
            # Block assessment
            #
            if blocks <= 50:
                block_status = {
                    "level": "pass",
                    "message": "Acceptable Size"
                }
            else:
                block_status = {
                    "level": "warning",
                    "message": "Bloated UI Graph"
                }

            #
            # Complexity assessment
            #
            if complexity <= 10:
                complexity_status = {
                    "level": "pass",
                    "message": "Low Risk"
                }

            elif complexity <= 20:
                complexity_status = {
                    "level": "warning",
                    "message": "Moderate Risk"
                }

            else:
                complexity_status = {
                    "level": "critical",
                    "message": "Refactor Immediately"
                }

                summary["high_risk_flows"].append(
                    {
                        "file_name": Path(
                            relative_path
                        ).name,
                        "complexity": complexity
                    }
                )

            flow_reports.append(
                {
                    "file_name": Path(
                        relative_path
                    ).name,

                    "relative_path": relative_path,

                    "metrics": {
                        "total_blocks":
                            blocks,

                        "total_edges":
                            metrics[
                                "total_edges"
                            ],

                        "mccabe_complexity":
                            complexity,

                        "decision_complexity":
                            metrics[
                                "cyclomatic_complexity_decision"
                            ],

                        "lambda_integrations":
                            metrics[
                                "lambda_integrations"
                            ],

                        "unhandled_error_blocks":
                            metrics[
                                "unhandled_error_blocks"
                            ]
                    },

                    "assessment": {
                        "block_status":
                            block_status,

                        "complexity_status":
                            complexity_status
                    }
                }
            )

            summary["successful_audits"] += 1

            summary["total_blocks"] += (
                metrics["total_blocks"]
            )

            summary["total_edges"] += (
                metrics["total_edges"]
            )

            summary["total_lambda_integrations"] += (
                metrics["lambda_integrations"]
            )

            summary["total_unhandled_error_blocks"] += (
                metrics["unhandled_error_blocks"]
            )

        except Exception as exc:

            summary["failed_audits"] += 1

            flow_reports.append(
                {
                    "file_name": Path(
                        relative_path
                    ).name,

                    "relative_path": relative_path,

                    "error": str(exc),

                    "assessment": {
                        "status": "failed"
                    }
                }
            )

    return {
        "summary": summary,
        "flows": flow_reports
    }

if __name__ == "__main__":
    mcp.run()