"""
Client for GitHub Models (https://github.com/marketplace/models) — an
OpenAI-compatible chat completions endpoint billed through your GitHub account.
This is the actual callable AI API in the "GitHub" ecosystem; GitHub Copilot
itself has no general-purpose endpoint for arbitrary text analysis.
"""
import json

import httpx

from .config import settings


class GitHubModelsError(RuntimeError):
    pass


async def chat_completion(model: str, prompt: str, temperature: float = 0.1) -> str:
    if not settings.github_token:
        raise GitHubModelsError(
            "GITHUB_TOKEN is not set. Create a fine-grained PAT with 'models: read' "
            "permission at https://github.com/settings/tokens and set it in backend/.env"
        )

    headers = {
        "Authorization": f"Bearer {settings.github_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(settings.github_models_endpoint, headers=headers, json=payload)

    if resp.status_code != 200:
        raise GitHubModelsError(f"GitHub Models call failed ({resp.status_code}): {resp.text}")

    data = resp.json()
    return data["choices"][0]["message"]["content"]


def parse_json_array(raw: str) -> list[dict]:
    """Models sometimes wrap JSON in markdown fences despite instructions — strip defensively."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned
    cleaned = cleaned.replace("json\n", "", 1) if cleaned.startswith("json\n") else cleaned
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []
