"""LangGraph Orchestrator for compliance review workflow."""
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

from langgraph.graph import StateGraph, END
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.database import AsyncSessionLocal
from app.db.models import Document, Review, ReviewStatus, DocumentStatus
from app.services.s3 import s3_service
from app.services.textract import textract_service
from app.services.websocket import ws_manager, send_review_event, ReviewEvent

from .base import AgentState
from .document_reviewer import DocumentReviewerAgent
from .specialists import (
    FINRASpecialistAgent,
    SECSpecialistAgent,
    CFPBSpecialistAgent,
    AMLKYCAgent,
    DataPrivacyAgent
)
from .core_agents import (
    RegulatoryExpertAgent,
    RiskAssessmentAgent,
    LegalWriterAgent,
    QualityAssuranceAgent,
    CitationValidatorAgent,
    AuditTrailAgent
)

logger = get_logger("orchestrator")


class ComplianceOrchestrator:
    """Orchestrates the 12-agent compliance review workflow using LangGraph."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("document_reviewer", self._run_document_reviewer)
        workflow.add_node("parallel_specialists", self._run_parallel_specialists)
        workflow.add_node("regulatory_expert", self._run_regulatory_expert)
        workflow.add_node("risk_assessment", self._run_risk_assessment)
        workflow.add_node("legal_writer", self._run_legal_writer)
        workflow.add_node("citation_validator", self._run_citation_validator)
        workflow.add_node("quality_assurance", self._run_quality_assurance)
        workflow.add_node("audit_trail", self._run_audit_trail)
        
        # Define the workflow edges
        workflow.set_entry_point("document_reviewer")
        workflow.add_edge("document_reviewer", "parallel_specialists")
        workflow.add_edge("parallel_specialists", "regulatory_expert")
        workflow.add_edge("regulatory_expert", "risk_assessment")
        workflow.add_edge("risk_assessment", "legal_writer")
        workflow.add_edge("legal_writer", "citation_validator")
        workflow.add_edge("citation_validator", "quality_assurance")
        workflow.add_edge("quality_assurance", "audit_trail")
        workflow.add_edge("audit_trail", END)
        
        return workflow.compile()
    
    async def _run_document_reviewer(self, state: AgentState) -> AgentState:
        """Run the Document Reviewer agent."""
        agent = DocumentReviewerAgent(self.db)
        return await agent.run(state)
    
    async def _run_specialist_with_own_session(self, agent_class, state: AgentState) -> AgentState:
        """Run a specialist agent with its own database session to avoid concurrent session issues."""
        async with AsyncSessionLocal() as db:
            agent = agent_class(db)
            return await agent.run(state)
    
    async def _run_parallel_specialists(self, state: AgentState) -> AgentState:
        """Run all 5 specialist agents SEQUENTIALLY to avoid timeouts and ensure reliability."""
        review_id = state["review_id"]
        
        # Define specialists with their names and findings keys
        specialists = [
            (FINRASpecialistAgent, "finra_specialist", "finra_findings"),
            (SECSpecialistAgent, "sec_specialist", "sec_findings"),
            (CFPBSpecialistAgent, "cfpb_specialist", "cfpb_findings"),
            (AMLKYCAgent, "aml_kyc_agent", "aml_findings"),
            (DataPrivacyAgent, "data_privacy_agent", "privacy_findings"),
        ]
        
        if "agents_completed" not in state:
            state["agents_completed"] = []
        if "errors" not in state:
            state["errors"] = []
        
        # Run each specialist SEQUENTIALLY - one at a time for reliability
        for agent_class, agent_name, findings_key in specialists:
            try:
                logger.info(f"Running {agent_name} sequentially...")
                result = await self._run_specialist_with_own_session(agent_class, state.copy())
                
                # Merge findings from this specialist
                if isinstance(result, dict):
                    if findings_key in result:
                        state[findings_key] = result[findings_key]
                    if "agents_completed" in result:
                        state["agents_completed"].extend(result["agents_completed"])
                
                logger.info(f"{agent_name} completed successfully")
                
            except Exception as e:
                logger.error(f"{agent_name} failed: {e}")
                state["errors"].append(f"{agent_name}: {str(e)}")
        
        # Update progress
        await send_review_event(
            ws_manager,
            review_id,
            ReviewEvent.REVIEW_PROGRESS,
            {
                "stage": "specialists_complete",
                "progress": 50,
                "agents_completed": state.get("agents_completed", [])
            }
        )
        
        return state
    
    async def _run_regulatory_expert(self, state: AgentState) -> AgentState:
        """Run the Regulatory Expert agent."""
        agent = RegulatoryExpertAgent(self.db)
        return await agent.run(state)
    
    async def _run_risk_assessment(self, state: AgentState) -> AgentState:
        """Run the Risk Assessment agent."""
        agent = RiskAssessmentAgent(self.db)
        return await agent.run(state)
    
    async def _run_legal_writer(self, state: AgentState) -> AgentState:
        """Run the Legal Writer agent."""
        agent = LegalWriterAgent(self.db)
        return await agent.run(state)
    
    async def _run_citation_validator(self, state: AgentState) -> AgentState:
        """Run the Citation Validator agent."""
        agent = CitationValidatorAgent(self.db)
        return await agent.run(state)
    
    async def _run_quality_assurance(self, state: AgentState) -> AgentState:
        """Run the Quality Assurance agent."""
        agent = QualityAssuranceAgent(self.db)
        return await agent.run(state)
    
    async def _run_audit_trail(self, state: AgentState) -> AgentState:
        """Run the Audit Trail agent."""
        agent = AuditTrailAgent(self.db)
        return await agent.run(state)
    
    async def run(self, initial_state: AgentState) -> AgentState:
        """
        Execute the full compliance review workflow.
        
        Args:
            initial_state: Initial state with document info
            
        Returns:
            Final state with all results
        """
        review_id = initial_state["review_id"]
        
        try:
            # Notify review started
            await send_review_event(
                ws_manager,
                review_id,
                ReviewEvent.REVIEW_STARTED,
                {"document_id": initial_state.get("document_id")}
            )
            
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Notify completion
            await send_review_event(
                ws_manager,
                review_id,
                ReviewEvent.REVIEW_COMPLETED,
                {
                    "compliance_score": final_state.get("compliance_score"),
                    "risk_score": final_state.get("risk_score"),
                    "violation_count": len(final_state.get("all_violations", []))
                }
            )
            
            return final_state
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            
            # Notify failure
            await send_review_event(
                ws_manager,
                review_id,
                ReviewEvent.REVIEW_FAILED,
                {"error": str(e)}
            )
            
            raise


async def run_compliance_review(document_id: str, review_id: str) -> None:
    """
    Run a complete compliance review for a document.
    
    This is the main entry point called from the API when a document is uploaded.
    
    Args:
        document_id: UUID of the document
        review_id: UUID of the review
    """
    logger.info(
        "starting_compliance_review",
        document_id=document_id,
        review_id=review_id
    )
    
    async with AsyncSessionLocal() as db:
        try:
            # Get document from database
            result = await db.execute(
                select(Document).where(Document.id == uuid.UUID(document_id))
            )
            document = result.scalar_one_or_none()
            
            if not document:
                logger.error(f"Document not found: {document_id}")
                return
            
            # Get review from database
            result = await db.execute(
                select(Review).where(Review.id == uuid.UUID(review_id))
            )
            review = result.scalar_one_or_none()
            
            if not review:
                logger.error(f"Review not found: {review_id}")
                return
            
            # Update document and review status
            document.status = DocumentStatus.PROCESSING
            review.status = ReviewStatus.IN_PROGRESS
            review.started_at = datetime.utcnow()
            await db.flush()
            
            # Download document from S3
            document_bytes = await s3_service.download_file(document.file_path)
            
            # Extract text using Textract
            extraction_result = await textract_service.extract_text_from_bytes(
                document_bytes=document_bytes,
                filename=document.original_filename
            )
            
            document_text = extraction_result.get("text", "")
            
            # Update document with extracted text
            document.extracted_text = document_text
            await db.flush()
            
            # Build initial state
            initial_state: AgentState = {
                "document_id": document_id,
                "review_id": review_id,
                "document_text": document_text,
                "filename": document.original_filename,
                "current_agent": "",
                "agents_completed": [],
                "errors": []
            }
            
            # Run the orchestrator
            orchestrator = ComplianceOrchestrator(db)
            final_state = await orchestrator.run(initial_state)
            
            # Update review with results
            review.status = ReviewStatus.COMPLETE
            review.completed_at = datetime.utcnow()
            review.compliance_score = final_state.get("compliance_score", 0)
            review.risk_score = final_state.get("risk_score", 0)
            review.summary = final_state.get("final_summary", "")
            
            # Update document status
            document.status = DocumentStatus.COMPLETE
            document.document_type = final_state.get("document_type")
            document.processed_at = datetime.utcnow()
            
            await db.commit()
            
            logger.info(
                "compliance_review_completed",
                document_id=document_id,
                review_id=review_id,
                compliance_score=review.compliance_score,
                risk_score=review.risk_score
            )
            
        except Exception as e:
            logger.error(f"Compliance review failed: {e}")
            
            # Update status to failed
            try:
                result = await db.execute(
                    select(Review).where(Review.id == uuid.UUID(review_id))
                )
                review = result.scalar_one_or_none()
                if review:
                    review.status = ReviewStatus.FAILED
                    review.error_message = str(e)
                    review.completed_at = datetime.utcnow()
                
                result = await db.execute(
                    select(Document).where(Document.id == uuid.UUID(document_id))
                )
                document = result.scalar_one_or_none()
                if document:
                    document.status = DocumentStatus.ERROR
                
                await db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update status: {update_error}")
            
            raise
