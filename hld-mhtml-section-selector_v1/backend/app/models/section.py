from __future__ import annotations

from pydantic import BaseModel, Field


class SectionNode(BaseModel):
    id: str
    title: str
    level: int = Field(ge=1, le=6)
    number: str | None = None
    page_label: str | None = None
    source: str
    children: list["SectionNode"] = Field(default_factory=list)


class ExtractSectionsResponse(BaseModel):
    document_name: str
    detection_strategy: str
    section_count: int
    sections: list[SectionNode]
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
