"""SQLAlchemy database models."""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Boolean, 
    ForeignKey, Enum, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from .database import Base


class DocumentStatus(str, PyEnum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


class ReviewStatus(str, PyEnum):
    """Review status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAILED = "failed"


class ViolationSeverity(str, PyEnum):
    """Violation severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    
    # Relationships
    documents: Mapped[List["Document"]] = relationship(back_populates="owner")


class Document(Base):
    """Uploaded document model."""
    __tablename__ = "documents"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)  # S3 key
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_type: Mapped[Optional[str]] = mapped_column(String(100))  # Detected type
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.PENDING
    )
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)
    doc_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)  # Renamed from metadata
    
    # Foreign keys
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    
    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    owner: Mapped["User"] = relationship(back_populates="documents")
    reviews: Mapped[List["Review"]] = relationship(back_populates="document")
    
    __table_args__ = (
        Index("idx_documents_owner_status", "owner_id", "status"),
    )


class Review(Base):
    """Compliance review model."""
    __tablename__ = "reviews"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus), default=ReviewStatus.PENDING
    )
    compliance_score: Mapped[Optional[int]] = mapped_column(Integer)  # 0-100
    risk_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-100
    summary: Mapped[Optional[str]] = mapped_column(Text)
    
    # Processing metadata
    processing_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Foreign keys
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    document: Mapped["Document"] = relationship(back_populates="reviews")
    violations: Mapped[List["Violation"]] = relationship(back_populates="review")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="review")
    bedrock_calls: Mapped[List["BedrockCallLog"]] = relationship(back_populates="review")
    
    __table_args__ = (
        Index("idx_reviews_status_created", "status", "created_at"),
    )


class Violation(Base):
    """Compliance violation model."""
    __tablename__ = "violations"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    regulation: Mapped[str] = mapped_column(String(255), nullable=False)
    regulation_code: Mapped[Optional[str]] = mapped_column(String(100))
    severity: Mapped[ViolationSeverity] = mapped_column(Enum(ViolationSeverity))
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Text references
    original_text: Mapped[Optional[str]] = mapped_column(Text)
    corrected_text: Mapped[Optional[str]] = mapped_column(Text)
    correction_explanation: Mapped[Optional[str]] = mapped_column(Text)
    
    # Location in document
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    start_position: Mapped[Optional[int]] = mapped_column(Integer)
    end_position: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Scores
    risk_score: Mapped[Optional[int]] = mapped_column(Integer)  # 1-100
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-1
    
    # Agent that identified it
    agent_source: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Citation validation
    citation_valid: Mapped[Optional[bool]] = mapped_column(Boolean)
    citation_url: Mapped[Optional[str]] = mapped_column(String(512))
    
    # Foreign keys
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    review: Mapped["Review"] = relationship(back_populates="violations")
    
    __table_args__ = (
        Index("idx_violations_review_severity", "review_id", "severity"),
    )


class AuditLog(Base):
    """Audit trail for agent actions."""
    __tablename__ = "audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # started, completed, failed
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Foreign keys
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id"), nullable=False
    )
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    review: Mapped["Review"] = relationship(back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_audit_logs_review_timestamp", "review_id", "timestamp"),
    )


class BedrockCallLog(Base):
    """AWS Bedrock API call logging."""
    __tablename__ = "bedrock_call_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Token usage
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Performance
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Request/Response payloads (can be large)
    request_payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    response_payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Status
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Foreign keys
    review_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reviews.id")
    )
    
    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # Relationships
    review: Mapped[Optional["Review"]] = relationship(back_populates="bedrock_calls")
    
    __table_args__ = (
        Index("idx_bedrock_calls_agent_timestamp", "agent_name", "timestamp"),
        Index("idx_bedrock_calls_review", "review_id"),
    )
