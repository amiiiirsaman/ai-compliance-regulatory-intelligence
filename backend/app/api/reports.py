"""Reports API endpoints for audit trails and exports."""
import uuid
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import Review, Document, AuditLog, Violation, BedrockCallLog, User
from app.api.auth import get_current_user
from app.services.s3 import s3_service

router = APIRouter()


# Pydantic models
class AuditLogEntry(BaseModel):
    id: str
    agent_name: str
    action: str
    status: str
    details: Optional[dict]
    error_message: Optional[str]
    duration_ms: Optional[int]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AuditTrailResponse(BaseModel):
    review_id: str
    document_id: str
    document_filename: str
    review_status: str
    created_at: datetime
    completed_at: Optional[datetime]
    total_duration_ms: Optional[int]
    audit_logs: List[AuditLogEntry]
    bedrock_summary: dict


class ViolationExport(BaseModel):
    regulation: str
    regulation_code: Optional[str]
    severity: str
    explanation: str
    original_text: Optional[str]
    corrected_text: Optional[str]
    page_number: Optional[int]
    risk_score: Optional[int]
    agent_source: str


class FullReportExport(BaseModel):
    export_date: datetime
    review_id: str
    document_filename: str
    compliance_score: Optional[int]
    risk_score: Optional[int]
    summary: Optional[str]
    violations: List[ViolationExport]
    audit_trail: List[AuditLogEntry]
    bedrock_usage: dict


# Routes
@router.get("/{review_id}/audit-trail", response_model=AuditTrailResponse)
async def get_audit_trail(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the complete audit trail for a review."""
    try:
        review_uuid = uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid review ID format"
        )
    
    result = await db.execute(
        select(Review)
        .where(Review.id == review_uuid)
        .options(
            selectinload(Review.document),
            selectinload(Review.audit_logs),
            selectinload(Review.bedrock_calls)
        )
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Verify ownership
    if review.document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Calculate total duration
    total_duration = None
    if review.started_at and review.completed_at:
        total_duration = int((review.completed_at - review.started_at).total_seconds() * 1000)
    
    # Build audit logs
    audit_logs = [
        AuditLogEntry(
            id=str(log.id),
            agent_name=log.agent_name,
            action=log.action,
            status=log.status,
            details=log.details,
            error_message=log.error_message,
            duration_ms=log.duration_ms,
            timestamp=log.timestamp
        )
        for log in sorted(review.audit_logs, key=lambda x: x.timestamp)
    ]
    
    # Summarize Bedrock usage
    bedrock_summary = {
        "total_calls": len(review.bedrock_calls),
        "successful_calls": sum(1 for c in review.bedrock_calls if c.success),
        "failed_calls": sum(1 for c in review.bedrock_calls if not c.success),
        "total_input_tokens": sum(c.input_tokens for c in review.bedrock_calls),
        "total_output_tokens": sum(c.output_tokens for c in review.bedrock_calls),
        "total_tokens": sum(c.total_tokens for c in review.bedrock_calls),
        "total_latency_ms": sum(c.latency_ms for c in review.bedrock_calls),
        "average_latency_ms": (
            sum(c.latency_ms for c in review.bedrock_calls) // len(review.bedrock_calls)
            if review.bedrock_calls else 0
        ),
        "by_agent": {}
    }
    
    # Group Bedrock usage by agent
    for call in review.bedrock_calls:
        if call.agent_name not in bedrock_summary["by_agent"]:
            bedrock_summary["by_agent"][call.agent_name] = {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "latency_ms": 0
            }
        agent_stats = bedrock_summary["by_agent"][call.agent_name]
        agent_stats["calls"] += 1
        agent_stats["input_tokens"] += call.input_tokens
        agent_stats["output_tokens"] += call.output_tokens
        agent_stats["latency_ms"] += call.latency_ms
    
    return AuditTrailResponse(
        review_id=str(review.id),
        document_id=str(review.document_id),
        document_filename=review.document.original_filename,
        review_status=review.status.value,
        created_at=review.created_at,
        completed_at=review.completed_at,
        total_duration_ms=total_duration,
        audit_logs=audit_logs,
        bedrock_summary=bedrock_summary
    )


@router.get("/{review_id}/audit-trail/download")
async def download_audit_trail(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download the audit trail as a JSON file."""
    # Reuse the get_audit_trail logic
    audit_trail = await get_audit_trail(review_id, db, current_user)
    
    # Convert to dict and serialize
    content = json.dumps(audit_trail.model_dump(), indent=2, default=str)
    
    filename = f"audit_trail_{review_id}.json"
    
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{review_id}/full-report")
async def get_full_report(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a full report including all violations, corrections, and audit trail."""
    try:
        review_uuid = uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid review ID format"
        )
    
    result = await db.execute(
        select(Review)
        .where(Review.id == review_uuid)
        .options(
            selectinload(Review.document),
            selectinload(Review.violations),
            selectinload(Review.audit_logs),
            selectinload(Review.bedrock_calls)
        )
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Verify ownership
    if review.document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build violations
    violations = [
        ViolationExport(
            regulation=v.regulation,
            regulation_code=v.regulation_code,
            severity=v.severity.value,
            explanation=v.explanation,
            original_text=v.original_text,
            corrected_text=v.corrected_text,
            page_number=v.page_number,
            risk_score=v.risk_score,
            agent_source=v.agent_source
        )
        for v in review.violations
    ]
    
    # Build audit logs
    audit_logs = [
        AuditLogEntry(
            id=str(log.id),
            agent_name=log.agent_name,
            action=log.action,
            status=log.status,
            details=log.details,
            error_message=log.error_message,
            duration_ms=log.duration_ms,
            timestamp=log.timestamp
        )
        for log in sorted(review.audit_logs, key=lambda x: x.timestamp)
    ]
    
    # Bedrock usage summary
    bedrock_usage = {
        "total_calls": len(review.bedrock_calls),
        "total_tokens": sum(c.total_tokens for c in review.bedrock_calls),
        "total_latency_ms": sum(c.latency_ms for c in review.bedrock_calls)
    }
    
    report = FullReportExport(
        export_date=datetime.utcnow(),
        review_id=str(review.id),
        document_filename=review.document.original_filename,
        compliance_score=review.compliance_score,
        risk_score=review.risk_score,
        summary=review.summary,
        violations=violations,
        audit_trail=audit_logs,
        bedrock_usage=bedrock_usage
    )
    
    return report


@router.get("/{review_id}/full-report/download")
async def download_full_report(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download the full report as a JSON file."""
    report = await get_full_report(review_id, db, current_user)
    
    content = json.dumps(report.model_dump(), indent=2, default=str)
    
    filename = f"compliance_report_{review_id}.json"
    
    return StreamingResponse(
        iter([content]),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{review_id}/annotated-pdf")
async def get_annotated_pdf_url(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get URL to download the annotated PDF with violations marked.
    
    Note: This returns metadata for client-side annotation rendering,
    as dynamic PDF annotation requires client-side processing.
    """
    try:
        review_uuid = uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid review ID format"
        )
    
    result = await db.execute(
        select(Review)
        .where(Review.id == review_uuid)
        .options(
            selectinload(Review.document),
            selectinload(Review.violations)
        )
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Verify ownership
    if review.document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get presigned URL for original PDF
    try:
        pdf_url = s3_service.get_presigned_url(
            s3_key=review.document.file_path,
            for_download=False
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF URL"
        )
    
    # Build annotation data for client-side rendering
    annotations = [
        {
            "id": str(v.id),
            "page": v.page_number or 1,
            "severity": v.severity.value,
            "regulation": v.regulation,
            "explanation": v.explanation,
            "original_text": v.original_text,
            "position": {
                "start": v.start_position,
                "end": v.end_position
            } if v.start_position else None
        }
        for v in review.violations
    ]
    
    return {
        "pdf_url": pdf_url,
        "filename": review.document.original_filename,
        "annotations": annotations,
        "total_violations": len(annotations)
    }
