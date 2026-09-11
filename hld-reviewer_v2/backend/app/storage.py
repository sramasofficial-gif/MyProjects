import json
import os
from dataclasses import asdict

from .config import settings
from .pdf_extractor import Chunk

os.makedirs(settings.storage_dir, exist_ok=True)


def _path(doc_id: str) -> str:
    return os.path.join(settings.storage_dir, f"{doc_id}.chunks.json")


def save_chunks(doc_id: str, chunks: list[Chunk]) -> None:
    with open(_path(doc_id), "w") as f:
        json.dump([asdict(c) for c in chunks], f)


def load_chunks(doc_id: str) -> list[Chunk] | None:
    path = _path(doc_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        raw = json.load(f)
    loaded = []
    for item in raw:
        c = Chunk(
            id=item["id"],
            section_type=item["section_type"],
            heading=item["heading"],
            text=item["text"],
            page_start=item["page_start"],
            page_end=item["page_end"],
        )
        loaded.append(c)
    return loaded
