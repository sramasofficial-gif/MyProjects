from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.section import ExtractSectionsResponse, HealthResponse
from app.parsers.mhtml_parser import MhtmlParseError, parse_mhtml_bytes
from app.parsers.section_extractor import count_sections, extract_sections

router = APIRouter()
MAX_FILE_SIZE = 25 * 1024 * 1024
ALLOWED_EXTENSIONS = {".mhtml", ".mht"}


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post(
    "/documents/extract-sections",
    response_model=ExtractSectionsResponse,
    status_code=status.HTTP_200_OK,
)
async def extract_document_sections(
    file: UploadFile = File(..., description="HLD document exported as MHTML/MHT"),
) -> ExtractSectionsResponse:
    filename = Path(file.filename or "document.mhtml").name
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .mhtml and .mht files are supported.",
        )

    data = await file.read(MAX_FILE_SIZE + 1)
    await file.close()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="The uploaded file exceeds the 25 MB limit.",
        )

    try:
        parsed = parse_mhtml_bytes(data)
        sections, strategy, warnings = extract_sections(parsed.html)
    except MhtmlParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The MHTML file could not be parsed.",
        ) from exc

    return ExtractSectionsResponse(
        document_name=filename,
        detection_strategy=strategy,
        section_count=count_sections(sections),
        sections=sections,
        warnings=warnings,
    )
