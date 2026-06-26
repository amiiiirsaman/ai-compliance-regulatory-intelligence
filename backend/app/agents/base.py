"""Base agent class and shared state definitions."""
import uuid as uuid_module
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict, Union
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.bedrock import bedrock_service
from app.services.websocket import ws_manager, send_review_event, ReviewEvent
from app.db.models import AuditLog, Violation, ViolationSeverity
from app.core.logging import get_logger


def to_uuid(value: Union[str, uuid_module.UUID]) -> uuid_module.UUID:
    """Convert string or UUID to UUID."""
    if isinstance(value, uuid_module.UUID):
        return value
    return uuid_module.UUID(value)


class AgentState(TypedDict, total=False):
    """Shared state passed between agents in the workflow."""
    # Document info
    document_id: str
    review_id: str
    document_text: str
    document_type: str
    filename: str
    
    # Processing state
    current_agent: str
    agents_completed: List[str]
    
    # Document analysis results
    document_summary: str
    risk_areas: List[str]
    
    # Regulatory findings from specialist agents
    finra_findings: List[Dict[str, Any]]
    sec_findings: List[Dict[str, Any]]
    cfpb_findings: List[Dict[str, Any]]
    aml_findings: List[Dict[str, Any]]
    privacy_findings: List[Dict[str, Any]]
    
    # Aggregated results
    all_violations: List[Dict[str, Any]]
    risk_score: int
    compliance_score: int
    
    # Corrections
    corrections: List[Dict[str, Any]]
    
    # Validation
    validated_violations: List[Dict[str, Any]]
    validation_status: str
    
    # Citations
    citation_results: List[Dict[str, Any]]
    
    # Final summary
    final_summary: str
    
    # Error tracking
    errors: List[str]


@dataclass
class AgentResult:
    """Result returned by an agent."""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: int = 0


class BaseAgent(ABC):
    """Base class for all compliance agents."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = get_logger(self.name)
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name identifier."""
        pass
    
    @property
    @abstractmethod
    def role(self) -> str:
        """Human-readable role description."""
        pass
    
    @property
    def system_prompt(self) -> str:
        """System prompt for the agent."""
        return f"""You are {self.role} in a compliance review system.
Your task is to analyze financial documents for regulatory compliance.
Be precise, thorough, and cite specific regulations when applicable.
Always respond in valid JSON format."""
    
    async def invoke_bedrock(
        self,
        prompt: str,
        review_id: str,
        max_tokens: int = 4096,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """Invoke Bedrock with logging and WebSocket updates."""
        # Notify via WebSocket
        await send_review_event(
            ws_manager,
            review_id,
            ReviewEvent.BEDROCK_CALL,
            {
                "agent_name": self.name,
                "status": "started"
            }
        )
        
        result = await bedrock_service.invoke_model(
            prompt=prompt,
            agent_name=self.name,
            review_id=review_id,
            db=self.db,
            system_prompt=self.system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Notify completion
        await send_review_event(
            ws_manager,
            review_id,
            ReviewEvent.BEDROCK_CALL,
            {
                "agent_name": self.name,
                "status": "completed",
                "latency_ms": result.get("latency_ms"),
                "tokens": result.get("input_tokens", 0) + result.get("output_tokens", 0)
            }
        )
        
        return result
    
    async def log_action(
        self,
        review_id: str,
        action: str,
        status: str,
        details: Optional[Dict] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> None:
        """Log an agent action to the audit trail."""
        audit_log = AuditLog(
            review_id=to_uuid(review_id),
            agent_name=self.name,
            action=action,
            status=status,
            details=details,
            error_message=error_message,
            duration_ms=duration_ms
        )
        self.db.add(audit_log)
        await self.db.commit()
    
    async def save_violation(
        self,
        review_id: str,
        regulation: str,
        severity: str,
        explanation: str,
        original_text: Optional[str] = None,
        corrected_text: Optional[str] = None,
        correction_explanation: Optional[str] = None,
        page_number: Optional[int] = None,
        risk_score: Optional[int] = None,
        confidence_score: Optional[float] = None,
        regulation_code: Optional[str] = None,
        citation_url: Optional[str] = None
    ) -> Violation:
        """Save a violation to the database."""
        violation = Violation(
            review_id=to_uuid(review_id),
            regulation=regulation,
            regulation_code=regulation_code,
            severity=ViolationSeverity(severity.lower()),
            explanation=explanation,
            original_text=original_text,
            corrected_text=corrected_text,
            correction_explanation=correction_explanation,
            page_number=page_number,
            risk_score=risk_score,
            confidence_score=confidence_score,
            agent_source=self.name,
            citation_url=citation_url
        )
        self.db.add(violation)
        await self.db.commit()
        
        # Notify via WebSocket
        await send_review_event(
            ws_manager,
            review_id,
            ReviewEvent.VIOLATION_FOUND,
            {
                "regulation": regulation,
                "severity": severity,
                "agent": self.name
            }
        )
        
        return violation
    
    @abstractmethod
    async def execute(self, state: AgentState) -> AgentState:
        """
        Execute the agent's task.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated workflow state
        """
        pass
    
    async def run(self, state: AgentState) -> AgentState:
        """Run the agent with error handling and logging."""
        review_id = state.get("review_id", "")
        start_time = datetime.utcnow()
        
        # Notify start
        await send_review_event(
            ws_manager,
            review_id,
            ReviewEvent.AGENT_STARTED,
            {"agent_name": self.name, "role": self.role}
        )
        
        await self.log_action(
            review_id=review_id,
            action="execute",
            status="started",
            details={"state_keys": list(state.keys())}
        )
        
        try:
            # Execute the agent
            result_state = await self.execute(state)
            
            # Calculate duration
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Log success
            await self.log_action(
                review_id=review_id,
                action="execute",
                status="completed",
                duration_ms=duration_ms
            )
            
            # Notify completion
            await send_review_event(
                ws_manager,
                review_id,
                ReviewEvent.AGENT_COMPLETED,
                {"agent_name": self.name, "duration_ms": duration_ms}
            )
            
            # Mark agent as completed
            if "agents_completed" not in result_state:
                result_state["agents_completed"] = []
            result_state["agents_completed"].append(self.name)
            
            return result_state
            
        except Exception as e:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            error_msg = str(e)
            
            self.logger.error(f"Agent execution failed: {error_msg}")
            
            # Log failure
            await self.log_action(
                review_id=review_id,
                action="execute",
                status="failed",
                error_message=error_msg,
                duration_ms=duration_ms
            )
            
            # Notify failure
            await send_review_event(
                ws_manager,
                review_id,
                ReviewEvent.AGENT_FAILED,
                {"agent_name": self.name, "error": error_msg}
            )
            
            # Add error to state
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"{self.name}: {error_msg}")
            
            return state
