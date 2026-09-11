import asyncio
from collections import defaultdict

from .checklist import (
    build_checklist_prompt,
    build_deep_review_prompt,
    build_selected_deep_review_prompt,
    build_selected_focus_prompt,
)
from .config import settings
from .focus_config import FOCUS_AREAS
from .github_models_client import chat_completion, parse_json_array
from .pdf_extractor import CHECKLIST_TYPES, Chunk


async def review_chunk(chunk: Chunk) -> dict:
    checklist_keys = CHECKLIST_TYPES.get(chunk.section_type, CHECKLIST_TYPES["unclassified"])

    # Stage 2 — cheap model, checklist screening
    prompt = build_checklist_prompt(chunk.heading, chunk.text, checklist_keys)
    raw = await chat_completion(settings.cheap_model, prompt)
    findings = parse_json_array(raw)

    escalate = [f for f in findings if f.get("needs_deep_review")]
    settled = [f for f in findings if not f.get("needs_deep_review")]

    deep_findings: list[dict] = []
    if escalate:
        # Stage 3 — only the flagged subset goes to the stronger, pricier model
        deep_prompt = build_deep_review_prompt(chunk.heading, chunk.text, escalate)
        deep_raw = await chat_completion(settings.strong_model, deep_prompt)
        deep_findings = parse_json_array(deep_raw)

    all_findings = settled + deep_findings
    for f in all_findings:
        f["chunk_id"] = chunk.id
        f["section"] = chunk.heading
        f["page_start"] = chunk.page_start
        f["page_end"] = chunk.page_end

    return {
        "chunk_id": chunk.id,
        "section": chunk.heading,
        "section_type": chunk.section_type,
        "escalated": bool(escalate),
        "findings": all_findings,
    }


async def _review_chunk_for_model_group(
    chunk: Chunk, model: str, focus_keys: list[str]
) -> list[dict]:
    """One call covers every focus area the user routed to this model for this section."""
    prompt = build_selected_focus_prompt(chunk.heading, chunk.text, focus_keys)
    raw = await chat_completion(model, prompt)
    findings = parse_json_array(raw)

    escalate = [f for f in findings if f.get("needs_deep_review")]
    settled = [f for f in findings if not f.get("needs_deep_review")]

    deep_findings: list[dict] = []
    if escalate:
        deep_prompt = build_selected_deep_review_prompt(chunk.heading, chunk.text, escalate)
        deep_raw = await chat_completion(model, deep_prompt)
        deep_findings = parse_json_array(deep_raw)

    all_findings = settled + deep_findings
    for f in all_findings:
        f["chunk_id"] = chunk.id
        f["section"] = chunk.heading
        f["page_start"] = chunk.page_start
        f["page_end"] = chunk.page_end
        f["model_used"] = model
    return all_findings


async def review_selected_chunks(
    chunks_by_id: dict[str, Chunk],
    selections: list[dict],
    model_assignment: dict[str, str],
    max_concurrency: int = 4,
) -> list[dict]:
    """
    Requirement-3 workflow. `selections` = [{"chunk_id": ..., "focus_areas": [...]}].
    `model_assignment` = {"security": "gpt-4o", "missing_sections": "gpt-4o-mini", ...}.
    Groups each section's chosen focus areas by assigned model so multiple focus
    areas on the same model become a single call instead of one call each.
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    results: list[dict] = []

    async def _process_section(selection: dict) -> dict:
        chunk = chunks_by_id.get(selection["chunk_id"])
        if chunk is None:
            return {"chunk_id": selection["chunk_id"], "error": "Unknown chunk_id", "findings": []}

        focus_keys = selection.get("focus_areas", [])
        by_model: dict[str, list[str]] = defaultdict(list)
        for key in focus_keys:
            model = model_assignment.get(key) or FOCUS_AREAS.get(key, {}).get("default_model", settings.cheap_model)
            by_model[model].append(key)

        async def _bounded_group(model: str, keys: list[str]) -> list[dict]:
            async with semaphore:
                return await _review_chunk_for_model_group(chunk, model, keys)

        group_results = await asyncio.gather(*(_bounded_group(m, ks) for m, ks in by_model.items()))
        findings = [f for group in group_results for f in group]

        return {
            "chunk_id": chunk.id,
            "section": chunk.heading,
            "section_type": chunk.section_type,
            "focus_areas_reviewed": focus_keys,
            "models_used": list(by_model.keys()),
            "findings": findings,
        }

    results = await asyncio.gather(*(_process_section(s) for s in selections))
    return list(results)


async def review_chunks(chunks: list[Chunk], max_concurrency: int = 4) -> list[dict]:
    """Review chunks concurrently, capped to avoid rate-limit spikes."""
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _bounded(chunk: Chunk) -> dict:
        async with semaphore:
            return await review_chunk(chunk)

    return await asyncio.gather(*(_bounded(c) for c in chunks))
