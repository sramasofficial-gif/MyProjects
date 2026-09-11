from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.models.section import ExtractSectionsResponse
from app.parsers.mhtml_parser import MhtmlParseError, parse_mhtml_bytes
from app.parsers.section_extractor import count_sections, extract_sections

router=APIRouter(); MAX=25*1024*1024
@router.get("/health")
async def health(): return {"status":"ok"}
@router.post("/documents/extract-sections",response_model=ExtractSectionsResponse)
async def extract(file: UploadFile=File(...)):
    name=Path(file.filename or "document.mhtml").name
    if Path(name).suffix.lower() not in {".mhtml",".mht"}: raise HTTPException(415,"Only .mhtml and .mht are supported.")
    data=await file.read(MAX+1); await file.close()
    if len(data)>MAX: raise HTTPException(413,"The file exceeds 25 MB.")
    try:
        parsed=parse_mhtml_bytes(data); sections,strategy,warnings=extract_sections(parsed.html)
    except MhtmlParseError as e: raise HTTPException(422,str(e)) from e
    return ExtractSectionsResponse(document_name=name,detection_strategy=strategy,section_count=count_sections(sections),sections=sections,warnings=warnings)
