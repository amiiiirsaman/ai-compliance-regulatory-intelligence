"""Document upload and management API endpoints."""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.database import get_db
from app.db.models import Document, DocumentStatus, Review, ReviewStatus, User
from app.api.auth import get_current_user
from app.services.s3 import s3_service

logger = get_logger("documents_api")

router = APIRouter()


# Pydantic models
class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    document_type: Optional[str]
    status: str
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    message: str
    document_id: str
    review_id: str


class PresignedUrlResponse(BaseModel):
    upload_url: str
    s3_key: str
    expires_in: int


# Helper functions
def validate_file_type(filename: str) -> bool:
    """Validate file extension is supported."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in settings.supported_file_types_list


def get_mime_type(filename: str) -> str:
    """Get MIME type from filename."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    mime_types = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain'
    }
    return mime_types.get(ext, 'application/octet-stream')


# Routes
@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document for compliance review.
    
    The document will be uploaded to S3 and a compliance review will be initiated
    asynchronously. Returns document_id and review_id for tracking.
    """
    # Validate file type
    if not validate_file_type(file.filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported types: {settings.SUPPORTED_FILE_TYPES}"
        )
    
    # Read file content
    content = await file.read()
    
    # Validate file size
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    # Get MIME type
    mime_type = get_mime_type(file.filename)
    
    # Upload to S3
    try:
        s3_key, s3_url = await s3_service.upload_file(
            file_content=content,
            filename=file.filename,
            user_id=str(current_user.id),
            content_type=mime_type
        )
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document"
        )
    
    # Create document record
    document = Document(
        filename=s3_key.split('/')[-1],
        original_filename=file.filename,
        file_path=s3_key,
        file_size=len(content),
        mime_type=mime_type,
        status=DocumentStatus.PENDING,
        owner_id=current_user.id
    )
    db.add(document)
    await db.commit()
    
    # Re-fetch document to get generated id
    from sqlalchemy import select as sa_select
    result = await db.execute(sa_select(Document).where(Document.file_path == s3_key))
    document = result.scalar_one()
    
    # Create review record
    review = Review(
        document_id=document.id,
        status=ReviewStatus.PENDING
    )
    db.add(review)
    await db.commit()
    
    # Re-fetch review
    result = await db.execute(sa_select(Review).where(Review.document_id == document.id))
    review = result.scalar_one()
    
    logger.info(
        "document_uploaded",
        document_id=str(document.id),
        review_id=str(review.id),
        filename=file.filename,
        size=len(content)
    )
    
    # Start background processing
    # This will be implemented in the agents module
    background_tasks.add_task(
        start_compliance_review,
        document_id=str(document.id),
        review_id=str(review.id)
    )
    
    return DocumentUploadResponse(
        message="Document uploaded and review process initiated.",
        document_id=str(document.id),
        review_id=str(review.id)
    )


@router.get("/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_upload_url(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a presigned URL for direct upload to S3.
    
    Use this for large files or client-side uploads.
    """
    if not validate_file_type(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported types: {settings.SUPPORTED_FILE_TYPES}"
        )
    
    mime_type = get_mime_type(filename)
    
    try:
        upload_url, s3_key = s3_service.get_presigned_upload_url(
            filename=filename,
            user_id=str(current_user.id),
            content_type=mime_type
        )
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL"
        )
    
    return PresignedUrlResponse(
        upload_url=upload_url,
        s3_key=s3_key,
        expires_in=settings.S3_PRESIGNED_URL_EXPIRY
    )


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents for the current user."""
    query = select(Document).where(Document.owner_id == current_user.id)
    
    if status:
        try:
            doc_status = DocumentStatus(status)
            query = query.where(Document.status == doc_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Valid values: {[s.value for s in DocumentStatus]}"
            )
    
    query = query.order_by(Document.uploaded_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return [
        DocumentResponse(
            id=str(doc.id),
            filename=doc.filename,
            original_filename=doc.original_filename,
            file_size=doc.file_size,
            mime_type=doc.mime_type,
            document_type=doc.document_type,
            status=doc.status.value,
            uploaded_at=doc.uploaded_at
        )
        for doc in documents
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    result = await db.execute(
        select(Document).where(
            Document.id == doc_uuid,
            Document.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse(
        id=str(document.id),
        filename=document.filename,
        original_filename=document.original_filename,
        file_size=document.file_size,
        mime_type=document.mime_type,
        document_type=document.document_type,
        status=document.status.value,
        uploaded_at=document.uploaded_at
    )


@router.get("/{document_id}/download-url")
async def get_document_download_url(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a presigned URL to download a document."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    result = await db.execute(
        select(Document).where(
            Document.id == doc_uuid,
            Document.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        download_url = s3_service.get_presigned_url(
            s3_key=document.file_path,
            for_download=True
        )
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download URL"
        )
    
    return {
        "download_url": download_url,
        "filename": document.original_filename,
        "expires_in": settings.S3_PRESIGNED_URL_EXPIRY
    }


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document and its associated reviews."""
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID format"
        )
    
    result = await db.execute(
        select(Document).where(
            Document.id == doc_uuid,
            Document.owner_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from S3
    try:
        await s3_service.delete_file(document.file_path)
    except Exception as e:
        logger.warning(f"Failed to delete file from S3: {e}")
    
    # Delete from database (cascades to reviews, violations, etc.)
    await db.delete(document)
    
    logger.info("document_deleted", document_id=document_id)


# Background task implementation
async def start_compliance_review(document_id: str, review_id: str):
    """
    Start the compliance review process.
    Calls the orchestrator to run the 12-agent workflow.
    """
    from app.agents.orchestrator import run_compliance_review
    
    logger.info(
        "compliance_review_started",
        document_id=document_id,
        review_id=review_id
    )
    
    # Run the compliance review workflow
    await run_compliance_review(document_id, review_id)
