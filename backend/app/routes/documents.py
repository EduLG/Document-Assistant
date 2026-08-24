import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import settings
from app.services.rag import ingest_pdf

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")

    dest_name = f"{uuid.uuid4().hex}_{file.filename}"
    dest_path = os.path.join(settings.upload_dir, dest_name)

    contents = await file.read()
    with open(dest_path, "wb") as f:
        f.write(contents)

    try:
        chunks_indexed = ingest_pdf(dest_path, source_name=file.filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al procesar el PDF: {exc}") from exc

    return {"filename": file.filename, "chunks_indexed": chunks_indexed}
