"""Document Reviewer Agent - The Analyst."""
import json
from typing import Any, Dict, List

from .base import BaseAgent, AgentState
from app.services.textract import textract_service


class DocumentReviewerAgent(BaseAgent):
    """Document Reviewer Agent - Extracts and analyzes document content."""
    
    @property
    def name(self) -> str:
        return "document_reviewer"
    
    @property
    def role(self) -> str:
        return "The Analyst - Document extraction and initial analysis specialist"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert document analyst specializing in financial and compliance documents.
Your role is to:
1. Identify the document type (prospectus, marketing material, disclosure, agreement, etc.)
2. Summarize the key content and purpose
3. Identify potential risk areas that require regulatory review
4. Flag any obvious compliance concerns

Respond in JSON format:
{
    "document_type": "string",
    "summary": "string",
    "key_topics": ["string"],
    "risk_areas": [
        {
            "area": "string",
            "description": "string",
            "potential_regulations": ["string"]
        }
    ],
    "initial_concerns": [
        {
            "concern": "string",
            "location": "string",
            "severity": "low|medium|high|critical"
        }
    ]
}"""
    
    async def extract_text(self, document_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Extract text from document using Textract."""
        try:
            result = await textract_service.extract_text_from_bytes(
                document_bytes=document_bytes,
                filename=filename
            )
            return result
        except Exception as e:
            self.logger.error(f"Textract extraction failed: {e}")
            # Fallback: return empty result
            return {"text": "", "pages": [], "confidence": 0}
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute document review and analysis."""
        review_id = state["review_id"]
        document_text = state.get("document_text", "")
        filename = state.get("filename", "document")
        
        if not document_text:
            state["errors"] = state.get("errors", [])
            state["errors"].append("No document text available for analysis")
            return state
        
        # Truncate text if too long for prompt
        max_chars = 50000
        analysis_text = document_text[:max_chars]
        if len(document_text) > max_chars:
            analysis_text += f"\n\n[Document truncated - {len(document_text) - max_chars} additional characters]"
        
        # Analyze document
        prompt = f"""Analyze the following financial/compliance document and provide a structured analysis.

Document filename: {filename}

Document content:
---
{analysis_text}
---

Provide your analysis in the required JSON format."""
        
        result = await self.invoke_bedrock(
            prompt=prompt,
            review_id=review_id,
            max_tokens=4096
        )
        
        # Parse response
        try:
            response_text = result.get("text", "{}")
            # Try to extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis = json.loads(response_text.strip())
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            analysis = {
                "document_type": "unknown",
                "summary": result.get("text", "")[:500],
                "key_topics": [],
                "risk_areas": [],
                "initial_concerns": []
            }
        
        # Update state
        state["document_type"] = analysis.get("document_type", "unknown")
        state["document_summary"] = analysis.get("summary", "")
        state["risk_areas"] = [
            r.get("area", "") for r in analysis.get("risk_areas", [])
        ]
        
        # Log initial concerns as potential findings
        for concern in analysis.get("initial_concerns", []):
            await self.log_action(
                review_id=review_id,
                action="initial_concern_identified",
                status="info",
                details=concern
            )
        
        return state
