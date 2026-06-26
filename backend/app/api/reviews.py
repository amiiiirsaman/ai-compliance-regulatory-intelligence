"""Reviews API endpoints."""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.database import get_db
from app.db.models import Review, ReviewStatus, Document, Violation, ViolationSeverity, User, BedrockCallLog
from app.api.auth import get_current_user

router = APIRouter()


# Pydantic models
class ViolationResponse(BaseModel):
    id: str
    regulation: str
    regulation_code: Optional[str]
    severity: str
    explanation: str
    original_text: Optional[str]
    corrected_text: Optional[str]
    correction_explanation: Optional[str]
    page_number: Optional[int]
    risk_score: Optional[int]
    confidence_score: Optional[float]
    agent_source: str
    citation_valid: Optional[bool]
    citation_url: Optional[str]
    
    class Config:
        from_attributes = True


class CorrectionResponse(BaseModel):
    original_text: str
    corrected_text: str
    explanation: Optional[str]
    regulation: str
    severity: str


class BedrockCallResponse(BaseModel):
    id: str
    agent_name: str
    model_id: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: int
    success: bool
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    review_id: str
    document_id: str
    document_filename: str
    status: str
    compliance_score: Optional[int]
    risk_score: Optional[int]
    summary: Optional[str]
    violations: List[ViolationResponse]
    corrections: List[CorrectionResponse]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


class ReviewListItem(BaseModel):
    review_id: str
    document_id: str
    document_filename: str
    status: str
    compliance_score: Optional[int]
    risk_score: Optional[int]
    violation_count: int
    created_at: datetime
    completed_at: Optional[datetime]


class ReviewProgressResponse(BaseModel):
    review_id: str
    status: str
    current_agent: Optional[str]
    progress_percentage: int
    agents_completed: List[str]
    bedrock_calls: List[BedrockCallResponse]


# Routes
@router.get("", response_model=List[ReviewListItem])
async def list_reviews(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all compliance reviews for the current user."""
    query = (
        select(Review)
        .join(Document)
        .where(Document.owner_id == current_user.id)
        .options(selectinload(Review.document), selectinload(Review.violations))
    )
    
    if status_filter:
        try:
            review_status = ReviewStatus(status_filter)
            query = query.where(Review.status == review_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Valid values: {[s.value for s in ReviewStatus]}"
            )
    
    query = query.order_by(Review.created_at.desc()).limit(limit).offset(offset)
    
    result = await db.execute(query)
    reviews = result.scalars().all()
    
    return [
        ReviewListItem(
            review_id=str(review.id),
            document_id=str(review.document_id),
            document_filename=review.document.original_filename,
            status=review.status.value,
            compliance_score=review.compliance_score,
            risk_score=review.risk_score,
            violation_count=len(review.violations),
            created_at=review.created_at,
            completed_at=review.completed_at
        )
        for review in reviews
    ]


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific compliance review with all details."""
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
    
    # Build violations response
    violations = [
        ViolationResponse(
            id=str(v.id),
            regulation=v.regulation,
            regulation_code=v.regulation_code,
            severity=v.severity.value,
            explanation=v.explanation,
            original_text=v.original_text,
            corrected_text=v.corrected_text,
            correction_explanation=v.correction_explanation,
            page_number=v.page_number,
            risk_score=v.risk_score,
            confidence_score=v.confidence_score,
            agent_source=v.agent_source,
            citation_valid=v.citation_valid,
            citation_url=v.citation_url
        )
        for v in review.violations
    ]
    
    # Build corrections from violations that have corrections
    corrections = [
        CorrectionResponse(
            original_text=v.original_text,
            corrected_text=v.corrected_text,
            explanation=v.correction_explanation,
            regulation=v.regulation,
            severity=v.severity.value
        )
        for v in review.violations
        if v.original_text and v.corrected_text
    ]
    
    return ReviewResponse(
        review_id=str(review.id),
        document_id=str(review.document_id),
        document_filename=review.document.original_filename,
        status=review.status.value,
        compliance_score=review.compliance_score,
        risk_score=review.risk_score,
        summary=review.summary,
        violations=violations,
        corrections=corrections,
        created_at=review.created_at,
        started_at=review.started_at,
        completed_at=review.completed_at,
        error_message=review.error_message
    )


@router.get("/{review_id}/progress", response_model=ReviewProgressResponse)
async def get_review_progress(
    review_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the progress of an ongoing review including Bedrock call logs."""
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
    
    # Get completed agents from Bedrock calls
    agents_completed = list(set(call.agent_name for call in review.bedrock_calls if call.success))
    
    # Calculate progress based on completed agents (12 total agents)
    total_agents = 12
    progress = int((len(agents_completed) / total_agents) * 100)
    
    # Determine current agent (last one called)
    current_agent = None
    if review.bedrock_calls:
        sorted_calls = sorted(review.bedrock_calls, key=lambda x: x.timestamp, reverse=True)
        current_agent = sorted_calls[0].agent_name
    
    # Build Bedrock calls response
    bedrock_calls = [
        BedrockCallResponse(
            id=str(call.id),
            agent_name=call.agent_name,
            model_id=call.model_id,
            input_tokens=call.input_tokens,
            output_tokens=call.output_tokens,
            total_tokens=call.total_tokens,
            latency_ms=call.latency_ms,
            success=call.success,
            timestamp=call.timestamp
        )
        for call in sorted(review.bedrock_calls, key=lambda x: x.timestamp)
    ]
    
    return ReviewProgressResponse(
        review_id=str(review.id),
        status=review.status.value,
        current_agent=current_agent,
        progress_percentage=progress,
        agents_completed=agents_completed,
        bedrock_calls=bedrock_calls
    )


@router.get("/{review_id}/violations", response_model=List[ViolationResponse])
async def get_review_violations(
    review_id: str,
    severity: Optional[str] = None,
    agent: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get violations for a review with optional filtering."""
    try:
        review_uuid = uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid review ID format"
        )
    
    # Verify review exists and user has access
    result = await db.execute(
        select(Review)
        .where(Review.id == review_uuid)
        .options(selectinload(Review.document))
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    if review.document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build query for violations
    query = select(Violation).where(Violation.review_id == review_uuid)
    
    if severity:
        try:
            sev = ViolationSeverity(severity)
            query = query.where(Violation.severity == sev)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity. Valid values: {[s.value for s in ViolationSeverity]}"
            )
    
    if agent:
        query = query.where(Violation.agent_source == agent)
    
    query = query.order_by(Violation.created_at)
    
    result = await db.execute(query)
    violations = result.scalars().all()
    
    return [
        ViolationResponse(
            id=str(v.id),
            regulation=v.regulation,
            regulation_code=v.regulation_code,
            severity=v.severity.value,
            explanation=v.explanation,
            original_text=v.original_text,
            corrected_text=v.corrected_text,
            correction_explanation=v.correction_explanation,
            page_number=v.page_number,
            risk_score=v.risk_score,
            confidence_score=v.confidence_score,
            agent_source=v.agent_source,
            citation_valid=v.citation_valid,
            citation_url=v.citation_url
        )
        for v in violations
    ]


@router.get("/{review_id}/bedrock-calls", response_model=List[BedrockCallResponse])
async def get_review_bedrock_calls(
    review_id: str,
    agent: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all Bedrock API call logs for a review."""
    try:
        review_uuid = uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid review ID format"
        )
    
    # Verify review exists and user has access
    result = await db.execute(
        select(Review)
        .where(Review.id == review_uuid)
        .options(selectinload(Review.document))
    )
    review = result.scalar_one_or_none()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    if review.document.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Build query for Bedrock calls
    query = select(BedrockCallLog).where(BedrockCallLog.review_id == review_uuid)
    
    if agent:
        query = query.where(BedrockCallLog.agent_name == agent)
    
    query = query.order_by(BedrockCallLog.timestamp)
    
    result = await db.execute(query)
    calls = result.scalars().all()
    
    return [
        BedrockCallResponse(
            id=str(call.id),
            agent_name=call.agent_name,
            model_id=call.model_id,
            input_tokens=call.input_tokens,
            output_tokens=call.output_tokens,
            total_tokens=call.total_tokens,
            latency_ms=call.latency_ms,
            success=call.success,
            timestamp=call.timestamp
        )
        for call in calls
    ]
