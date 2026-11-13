import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.services.pdf_service import extract_text_from_pdf


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024
UPLOAD_CHUNK_SIZE = 1024 * 1024


class DocumentCreate(BaseModel):
    title: str
    content: str
    source: str
    source_type: str = "web"


class DocumentUpdate(BaseModel):
    title: str
    content: str
    source: str
    source_type: str = "web"


@router.post("")
def create_document(
    document_data: DocumentCreate,
    db: Session = Depends(get_db),
):
    if not document_data.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty",
        )

    if not document_data.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Content cannot be empty",
        )

    if not document_data.source.strip():
        raise HTTPException(
            status_code=400,
            detail="Source cannot be empty",
        )

    document = Document(
        title=document_data.title.strip(),
        content=document_data.content.strip(),
        source=document_data.source.strip(),
        source_type=document_data.source_type.strip(),
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "message": "Document created successfully",
        "document": {
            "id": document.id,
            "title": document.title,
            "source": document.source,
            "source_type": document.source_type,
        },
    }


@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected",
        )

    # Normalize the supplied filename and remove directory components.
    original_name = Path(
        file.filename.replace("\\", "/")
    ).name

    if not original_name.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    # Keep a safe display name; never use it as the storage path.
    safe_name = re.sub(
        r"[^\w.\- ]",
        "_",
        original_name,
        flags=re.UNICODE,
    ).strip(" .")

    if not safe_name or safe_name.lower() == ".pdf":
        safe_name = "uploaded_document.pdf"

    title = Path(safe_name).stem or "Uploaded document"

    project_root = Path(__file__).resolve().parents[3]
    upload_directory = project_root / "data" / "raw"
    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    # A unique generated name prevents path traversal and overwriting.
    stored_filename = f"{uuid4().hex}.pdf"
    file_path = upload_directory / stored_filename

    total_size = 0

    try:
        # Stream the upload in chunks to avoid loading the whole file
        # into memory.
        with open(file_path, "wb") as pdf_file:
            while True:
                chunk = await file.read(UPLOAD_CHUNK_SIZE)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_PDF_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="PDF file exceeds the 10 MB upload limit",
                    )

                pdf_file.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded PDF is empty",
            )

        # Extract text separately so invalid PDFs receive a client error.
        try:
            extracted_text = extract_text_from_pdf(str(file_path))
        except Exception:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unable to read this PDF. "
                    "The file may be corrupted or contain no readable text."
                ),
            )

        document = Document(
            title=title,
            content=extracted_text,
            source=f"upload://{stored_filename}",
            source_type="pdf",
        )

        try:
            db.add(document)
            db.commit()
            db.refresh(document)
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Failed to save the uploaded document.",
            )

        return {
            "message": "PDF uploaded and indexed successfully",
            "document": {
                "id": document.id,
                "title": document.title,
                "source": document.source,
                "source_type": document.source_type,
                "content_length": len(document.content),
            },
        }

    except HTTPException:
        # Remove incomplete or rejected uploads.
        if file_path.exists():
            file_path.unlink()
        raise

    except Exception:
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while uploading the PDF.",
        )

    finally:
        await file.close()


@router.get("")
def get_documents(
    db: Session = Depends(get_db),
):
    documents = db.query(Document).all()

    return {
        "count": len(documents),
        "documents": [
            {
                "id": document.id,
                "title": document.title,
                "content": document.content,
                "source": document.source,
                "source_type": document.source_type,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
            }
            for document in documents
        ],
    }


@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return {
        "id": document.id,
        "title": document.title,
        "content": document.content,
        "source": document.source,
        "source_type": document.source_type,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
    }


@router.put("/{document_id}")
def update_document(
    document_id: int,
    document_data: DocumentUpdate,
    db: Session = Depends(get_db),
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if not document_data.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Title cannot be empty",
        )

    if not document_data.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Content cannot be empty",
        )

    if not document_data.source.strip():
        raise HTTPException(
            status_code=400,
            detail="Source cannot be empty",
        )

    document.title = document_data.title.strip()
    document.content = document_data.content.strip()
    document.source = document_data.source.strip()
    document.source_type = document_data.source_type.strip()

    db.commit()
    db.refresh(document)

    return {
        "message": "Document updated successfully",
        "document": {
            "id": document.id,
            "title": document.title,
            "source": document.source,
            "source_type": document.source_type,
        },
    }


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    db.delete(document)
    db.commit()

    return {
        "message": "Document deleted successfully",
        "deleted_document_id": document_id,
    }