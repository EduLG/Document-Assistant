import os
import uuid

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import settings
from app.services.loaders import SUPPORTED_EXTENSIONS
from app.services.rag import ingest_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_documents(files: list[UploadFile]):
    for file in files:
        extension = os.path.splitext(file.filename)[1].lower()
        if extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file type '{extension}' for '{file.filename}'. "
                    f"Allowed: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
                ),
            )

    results = []
    for file in files:
        dest_name = f"{uuid.uuid4().hex}_{file.filename}"
        dest_path = os.path.join(settings.upload_dir, dest_name)

        contents = await file.read()
        with open(dest_path, "wb") as f:
            f.write(contents)

        try:
            chunks_indexed = ingest_document(dest_path, source_name=file.filename)
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=f"Error processing '{file.filename}': {exc}"
            ) from exc

        results.append({"filename": file.filename, "chunks_indexed": chunks_indexed})

    return results
