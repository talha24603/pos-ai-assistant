from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import Form

from app.services.pdf_extractor import (
    extract_text_from_pdf
)

from app.services.document_ingestor import (
    ingest_document
)

router = APIRouter()


@router.post("/documents/upload")
async def upload_document(

    tenant_id: str = Form(...),

    file: UploadFile = File(...)
):

    if not file.filename.endswith(".pdf"):

        return {
            "error": "Only PDF files allowed"
        }

    text = extract_text_from_pdf(
        file.file
    )

    ingest_document(
        tenant_id=tenant_id,
        document_name=file.filename,
        content=text
    )

    return {
        "message": "Document processed successfully",
        "filename": file.filename
    }