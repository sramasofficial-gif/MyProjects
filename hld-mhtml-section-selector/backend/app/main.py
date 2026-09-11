from pathlib import Path
from fastapi import FastAPI,UploadFile,File,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.section import ExtractResponse
from app.parsers.mhtml import extract_html,MhtmlError
from app.parsers.extractor import extract_sections,count
app=FastAPI(title='HLD section extractor',version='3.0')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173'],allow_methods=['*'],allow_headers=['*'])
@app.post('/api/v1/documents/extract-sections',response_model=ExtractResponse)
async def extract(file:UploadFile=File(...)):
    name=Path(file.filename or 'document.mhtml').name
    if Path(name).suffix.lower() not in {'.mhtml','.mht'}:raise HTTPException(415,'Only .mhtml and .mht are supported.')
    data=await file.read(25*1024*1024+1)
    if len(data)>25*1024*1024:raise HTTPException(413,'File exceeds 25 MB.')
    try:sections,strategy,warnings=extract_sections(extract_html(data))
    except MhtmlError as e:raise HTTPException(422,str(e))
    return ExtractResponse(document_name=name,detection_strategy=strategy,section_count=count(sections),sections=sections,warnings=warnings)
