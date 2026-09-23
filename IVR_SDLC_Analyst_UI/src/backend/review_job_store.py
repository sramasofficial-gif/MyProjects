from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 500


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _json(value: Any, default: Any) -> str:
    try:
        return json.dumps(value if value is not None else default, ensure_ascii=False, separators=(",", ":"))
    except TypeError:
        return json.dumps(default, ensure_ascii=False, separators=(",", ":"))


def _loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


class ReviewJobStore:
    """SQLite-backed durable repository for Technical Document Review jobs.

    SQLite is used as the system of record. The class intentionally returns
    plain Python dictionaries so the existing FastAPI review worker can keep
    using the same in-memory job shape without a broad rewrite.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.db_path,
            timeout=15,
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.execute("PRAGMA busy_timeout = 15000")
        return connection

    def _initialize(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS schema_info (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            schema_version INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS review_jobs (
            job_id TEXT PRIMARY KEY,
            document_url TEXT NOT NULL,
            document_title TEXT NOT NULL,
            source_version TEXT,
            source_version_timestamp TEXT,
            source_version_source TEXT,
            source_content_hash TEXT,
            review_type TEXT NOT NULL DEFAULT 'Technical Document Review',
            project_scope TEXT,
            review_scopes_json TEXT NOT NULL DEFAULT '[]',
            selected_section_ids_json TEXT NOT NULL DEFAULT '[]',
            eligible_section_ids_json TEXT NOT NULL DEFAULT '[]',
            review_signature TEXT,
            review_signature_version INTEGER,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            updated_at TEXT NOT NULL,
            duration_ms INTEGER NOT NULL DEFAULT 0,
            input_tokens INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            reasoning_tokens INTEGER NOT NULL DEFAULT 0,
            ai_credits REAL NOT NULL DEFAULT 0,
            model_calls INTEGER NOT NULL DEFAULT 0,
            finding_count INTEGER NOT NULL DEFAULT 0,
            pass_count INTEGER NOT NULL DEFAULT 0,
            manual_review_count INTEGER NOT NULL DEFAULT 0,
            actual_models_json TEXT NOT NULL DEFAULT '[]',
            auto_tiers_json TEXT NOT NULL DEFAULT '[]',
            progress_json TEXT NOT NULL DEFAULT '{}',
            usage_json TEXT NOT NULL DEFAULT '{}',
            review_plan_json TEXT NOT NULL DEFAULT '{}',
            result_json TEXT,
            review_errors_json TEXT NOT NULL DEFAULT '[]',
            error TEXT,
            recovery_note TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_review_jobs_status_updated
            ON review_jobs(status, updated_at DESC);

        CREATE INDEX IF NOT EXISTS idx_review_jobs_document_updated
            ON review_jobs(document_url, updated_at DESC);

        CREATE INDEX IF NOT EXISTS idx_review_jobs_signature_updated
            ON review_jobs(review_signature, updated_at DESC);
        """
        with self._lock, self._connect() as connection:
            connection.executescript(schema)
            connection.execute(
                "INSERT OR IGNORE INTO schema_info(id, schema_version) VALUES(1, ?)",
                (SCHEMA_VERSION,),
            )
            connection.commit()

    def _row_to_job(self, row: sqlite3.Row | None) -> dict | None:
        if row is None:
            return None
        job = dict(row)
        for key in (
            "review_scopes_json",
            "selected_section_ids_json",
            "eligible_section_ids_json",
            "actual_models_json",
            "auto_tiers_json",
            "progress_json",
            "usage_json",
            "review_plan_json",
            "review_errors_json",
        ):
            value = job.pop(key, None)
            mapped = {
                "review_scopes_json": "review_scopes",
                "selected_section_ids_json": "selected_section_ids",
                "eligible_section_ids_json": "eligible_section_ids",
                "actual_models_json": "actual_models",
                "auto_tiers_json": "auto_tiers",
                "progress_json": "progress",
                "usage_json": "usage",
                "review_plan_json": "review_plan",
                "review_errors_json": "review_errors",
            }[key]
            default = [] if mapped in {
                "review_scopes",
                "selected_section_ids",
                "eligible_section_ids",
                "actual_models",
                "auto_tiers",
                "review_errors",
            } else {}
            job[mapped] = _loads(value, default)
        if job.get("result_json") is not None:
            job["result"] = _loads(job.pop("result_json"), None)
        else:
            job.pop("result_json", None)
            job["result"] = None
        job["selected_section_ids"] = [int(x) for x in (job.get("selected_section_ids") or []) if str(x).strip()]
        job["eligible_section_ids"] = [int(x) for x in (job.get("eligible_section_ids") or []) if str(x).strip()]
        job["duration_ms"] = int(job.get("duration_ms") or 0)
        job["input_tokens"] = int(job.get("input_tokens") or 0)
        job["output_tokens"] = int(job.get("output_tokens") or 0)
        job["reasoning_tokens"] = int(job.get("reasoning_tokens") or 0)
        job["model_calls"] = int(job.get("model_calls") or 0)
        job["finding_count"] = int(job.get("finding_count") or 0)
        job["pass_count"] = int(job.get("pass_count") or 0)
        job["manual_review_count"] = int(job.get("manual_review_count") or 0)
        job["ai_credits"] = float(job.get("ai_credits") or 0)
        return job

    def upsert_job(self, job: dict) -> dict:
        if not job.get("job_id"):
            raise ValueError("Review job must contain job_id")

        now = utc_now()
        job["updated_at"] = now

        selected_ids = [int(x) for x in job.get("selected_section_ids") or []]
        eligible_ids = [int(x) for x in job.get("eligible_section_ids") or []]
        review_scopes = list(job.get("review_scopes") or [])
        actual_models = list(job.get("actual_models") or [])
        auto_tiers = list(job.get("auto_tiers") or [])
        progress = job.get("progress") or {}
        usage = job.get("usage") or {}
        review_plan = job.get("review_plan") or {}
        review_errors = job.get("review_errors") or []
        result = job.get("result")

        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO review_jobs (
                    job_id, document_url, document_title,
                    source_version, source_version_timestamp, source_version_source,
                    source_content_hash, review_type, project_scope,
                    review_scopes_json, selected_section_ids_json,
                    eligible_section_ids_json, review_signature, review_signature_version,
                    status, created_at, started_at, completed_at, updated_at,
                    duration_ms, input_tokens, output_tokens, reasoning_tokens,
                    ai_credits, model_calls, finding_count, pass_count, manual_review_count,
                    actual_models_json, auto_tiers_json, progress_json, usage_json,
                    review_plan_json, result_json, review_errors_json, error, recovery_note
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                ON CONFLICT(job_id) DO UPDATE SET
                    document_url=excluded.document_url,
                    document_title=excluded.document_title,
                    source_version=excluded.source_version,
                    source_version_timestamp=excluded.source_version_timestamp,
                    source_version_source=excluded.source_version_source,
                    source_content_hash=excluded.source_content_hash,
                    review_type=excluded.review_type,
                    project_scope=excluded.project_scope,
                    review_scopes_json=excluded.review_scopes_json,
                    selected_section_ids_json=excluded.selected_section_ids_json,
                    eligible_section_ids_json=excluded.eligible_section_ids_json,
                    review_signature=excluded.review_signature,
                    review_signature_version=excluded.review_signature_version,
                    status=excluded.status,
                    created_at=excluded.created_at,
                    started_at=excluded.started_at,
                    completed_at=excluded.completed_at,
                    updated_at=excluded.updated_at,
                    duration_ms=excluded.duration_ms,
                    input_tokens=excluded.input_tokens,
                    output_tokens=excluded.output_tokens,
                    reasoning_tokens=excluded.reasoning_tokens,
                    ai_credits=excluded.ai_credits,
                    model_calls=excluded.model_calls,
                    finding_count=excluded.finding_count,
                    pass_count=excluded.pass_count,
                    manual_review_count=excluded.manual_review_count,
                    actual_models_json=excluded.actual_models_json,
                    auto_tiers_json=excluded.auto_tiers_json,
                    progress_json=excluded.progress_json,
                    usage_json=excluded.usage_json,
                    review_plan_json=excluded.review_plan_json,
                    result_json=excluded.result_json,
                    review_errors_json=excluded.review_errors_json,
                    error=excluded.error,
                    recovery_note=excluded.recovery_note
                """,
                (
                    str(job["job_id"]),
                    str(job.get("document_url") or job.get("document_title") or ""),
                    str(job.get("document_title") or ""),
                    job.get("source_version"),
                    job.get("source_version_timestamp"),
                    job.get("source_version_source"),
                    job.get("source_content_hash"),
                    job.get("review_type") or "Technical Document Review",
                    job.get("project_scope"),
                    _json(review_scopes, []),
                    _json(selected_ids, []),
                    _json(eligible_ids, []),
                    job.get("review_signature"),
                    job.get("review_signature_version"),
                    job.get("status") or "UNKNOWN",
                    job.get("created_at") or now,
                    job.get("started_at"),
                    job.get("completed_at"),
                    now,
                    int(job.get("duration_ms") or 0),
                    int(job.get("input_tokens") or (usage.get("input_tokens") or usage.get("inputTokens") or 0)),
                    int(job.get("output_tokens") or (usage.get("output_tokens") or usage.get("outputTokens") or 0)),
                    int(job.get("reasoning_tokens") or (usage.get("reasoning_tokens") or usage.get("reasoningTokens") or 0)),
                    float(job.get("ai_credits") or usage.get("ai_credits") or usage.get("aiCredits") or 0),
                    int(job.get("model_calls") or usage.get("model_calls") or usage.get("modelCalls") or 0),
                    int(job.get("finding_count") or 0),
                    int(job.get("pass_count") or 0),
                    int(job.get("manual_review_count") or 0),
                    _json(actual_models, []),
                    _json(auto_tiers, []),
                    _json(progress, {}),
                    _json(usage, {}),
                    _json(review_plan, {}),
                    _json(result, None) if result is not None else None,
                    _json(review_errors, []),
                    job.get("error"),
                    job.get("recovery_note"),
                ),
            )
            connection.commit()
        return self.get_job(job["job_id"]) or dict(job)

    def get_job(self, job_id: str) -> dict | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM review_jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        return self._row_to_job(row)

    def list_jobs(
        self,
        *,
        status: str | None = None,
        document_url: str | None = None,
        search: str | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        limit = max(1, min(int(limit), MAX_PAGE_SIZE))
        offset = max(0, int(offset))
        clauses = []
        params: list[Any] = []

        if status:
            clauses.append("status = ?")
            params.append(status.upper())
        if document_url:
            clauses.append("document_url = ?")
            params.append(document_url)
        if search:
            clauses.append("(job_id LIKE ? OR document_title LIKE ? OR document_url LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like, like])

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._lock, self._connect() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) AS count FROM review_jobs {where}",
                params,
            ).fetchone()["count"]
            rows = connection.execute(
                f"SELECT * FROM review_jobs {where} ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()
        return [self._row_to_job(row) for row in rows], int(total)

    def find_latest(
        self,
        *,
        document_url: str,
        review_signature: str,
    ) -> dict | None:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM review_jobs
                WHERE document_url = ? AND review_signature = ?
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (document_url, review_signature),
            ).fetchone()
        return self._row_to_job(row)

    def delete_job(self, job_id: str) -> bool:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM review_jobs WHERE job_id = ? AND status IN ('COMPLETED','FAILED','CANCELLED')",
                (job_id,),
            )
            connection.commit()
            return cursor.rowcount > 0

    def delete_completed(self, job_ids: list[str] | None = None) -> int:
        with self._lock, self._connect() as connection:
            if job_ids:
                placeholders = ",".join("?" for _ in job_ids)
                cursor = connection.execute(
                    f"DELETE FROM review_jobs WHERE status = 'COMPLETED' AND job_id IN ({placeholders})",
                    [str(x) for x in job_ids],
                )
            else:
                cursor = connection.execute(
                    "DELETE FROM review_jobs WHERE status = 'COMPLETED'"
                )
            connection.commit()
            return int(cursor.rowcount)

    def migrate_json_directory(self, directory: str | Path) -> int:
        """One-time migration of legacy JSON review jobs into SQLite."""
        directory = Path(directory)
        if not directory.exists():
            return 0
        migrated = 0
        for path in directory.glob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as handle:
                    job = json.load(handle)
                if not job.get("job_id"):
                    continue
                if self.get_job(str(job.get("job_id"))) is None:
                    self.upsert_job(job)
                    migrated += 1
            except (OSError, ValueError, TypeError, sqlite3.Error):
                continue
        return migrated
