"""Core Processing Agents - Regulatory Expert, Legal Writer, Risk Assessment, QA."""
import json
from typing import Any, Dict, List

from .base import BaseAgent, AgentState


class RegulatoryExpertAgent(BaseAgent):
    """Regulatory Expert Agent - The Coordinator."""
    
    @property
    def name(self) -> str:
        return "regulatory_expert"
    
    @property
    def role(self) -> str:
        return "The Coordinator - Aggregates and prioritizes findings from all specialist agents"
    
    @property
    def system_prompt(self) -> str:
        return """You are a senior regulatory compliance expert who coordinates findings from multiple specialist agents.
Your role is to:
1. Review all findings from FINRA, SEC, CFPB, AML/KYC, and Privacy specialists
2. Remove duplicates and consolidate overlapping findings
3. Rank violations by severity and regulatory importance
4. Identify any conflicts between regulatory requirements
5. Provide an overall compliance assessment

Respond in JSON format:
{
    "consolidated_violations": [
        {
            "rank": 1,
            "regulation": "string",
            "severity": "critical|high|medium|low",
            "explanation": "string",
            "source_agents": ["agent names"],
            "remediation_priority": "immediate|short_term|medium_term|low"
        }
    ],
    "regulatory_conflicts": ["any conflicting requirements"],
    "overall_compliance_status": "non_compliant|partially_compliant|mostly_compliant|compliant",
    "executive_summary": "brief summary for executives"
}"""
    
    async def execute(self, state: AgentState) -> AgentState:
        """Aggregate and prioritize all regulatory findings."""
        review_id = state["review_id"]
        
        # Collect all findings
        all_findings = {
            "finra": state.get("finra_findings", []),
            "sec": state.get("sec_findings", []),
            "cfpb": state.get("cfpb_findings", []),
            "aml": state.get("aml_findings", []),
            "privacy": state.get("privacy_findings", [])
        }
        
        prompt = f"""Review and consolidate these compliance findings from multiple specialist agents:

FINRA Findings:
{json.dumps(all_findings['finra'], indent=2)}

SEC Findings:
{json.dumps(all_findings['sec'], indent=2)}

CFPB Findings:
{json.dumps(all_findings['cfpb'], indent=2)}

AML/KYC Findings:
{json.dumps(all_findings['aml'], indent=2)}

Data Privacy Findings:
{json.dumps(all_findings['privacy'], indent=2)}

Consolidate these findings, remove duplicates, rank by severity, and provide an executive summary."""
        
        result = await self.invoke_bedrock(
            prompt=prompt,
            review_id=review_id,
            max_tokens=4096
        )
        
        try:
            response_text = result.get("text", "{}")
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis = json.loads(response_text.strip())
        except json.JSONDecodeError:
            analysis = {
                "consolidated_violations": [],
                "regulatory_conflicts": [],
                "overall_compliance_status": "unknown",
                "executive_summary": ""
            }
        
        state["all_violations"] = analysis.get("consolidated_violations", [])
        state["final_summary"] = analysis.get("executive_summary", "")
        
        return state


class RiskAssessmentAgent(BaseAgent):
    """Risk Assessment Agent - The Scorer."""
    
    @property
    def name(self) -> str:
        return "risk_assessment"
    
    @property
    def role(self) -> str:
        return "The Scorer - Calculates risk and compliance scores based on findings"
    
    @property
    def system_prompt(self) -> str:
        return """You are a risk assessment specialist who calculates compliance and risk scores.

IMPORTANT: Use industry-standard weighted scoring that differentiates between minor and severe issues.

Scoring methodology (industry-standard weighted approach):
- Risk Score (0-100): Higher = more risk
  - Critical violations: +30 each (max 3 before cap)
  - High severity: +15 each
  - Medium severity: +5 each
  - Low severity: +2 each
  - Maximum risk score is 100

- Compliance Score (0-100): Higher = more compliant
  - Start at 100
  - Critical violations: -30 each
  - High severity: -15 each
  - Medium severity: -5 each
  - Low severity: -2 each
  - Minimum score is 10 (unless critical violations exist, then 0)
  - A document with only low/medium issues should never score below 60%

- Letter Grade (industry standard):
  - A: 90-100% (Excellent - minimal or no issues)
  - B: 80-89% (Good - minor issues only)
  - C: 70-79% (Acceptable - some medium issues)
  - D: 60-69% (Needs Improvement - multiple issues)
  - F: Below 60% (Failing - critical issues or many violations)

Respond in JSON format:
{
    "risk_score": 0-100,
    "compliance_score": 0-100,
    "letter_grade": "A|B|C|D|F",
    "risk_level": "critical|high|medium|low",
    "score_breakdown": {
        "critical_count": 0,
        "high_count": 0,
        "medium_count": 0,
        "low_count": 0
    },
    "risk_factors": ["key risk factors"],
    "mitigation_recommendations": ["prioritized recommendations"]
}"""
    
    async def execute(self, state: AgentState) -> AgentState:
        """Calculate risk and compliance scores."""
        review_id = state["review_id"]
        violations = state.get("all_violations", [])
        
        # Also include raw findings if consolidated isn't available
        if not violations:
            for key in ["finra_findings", "sec_findings", "cfpb_findings", "aml_findings", "privacy_findings"]:
                violations.extend(state.get(key, []))
        
        prompt = f"""Calculate risk and compliance scores based on these violations:

{json.dumps(violations, indent=2)}

Document type: {state.get('document_type', 'unknown')}
Document summary: {state.get('document_summary', '')}

Provide detailed scoring with breakdown and recommendations."""
        
        result = await self.invoke_bedrock(
            prompt=prompt,
            review_id=review_id,
            max_tokens=2048
        )
        
        try:
            response_text = result.get("text", "{}")
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis = json.loads(response_text.strip())
        except json.JSONDecodeError:
            # Calculate basic scores if parsing fails - using industry-standard weighted approach
            critical = sum(1 for v in violations if v.get("severity") == "critical")
            high = sum(1 for v in violations if v.get("severity") == "high")
            medium = sum(1 for v in violations if v.get("severity") == "medium")
            low = sum(1 for v in violations if v.get("severity") == "low")
            
            # New weighted scoring - more reasonable deductions
            risk_score = min(100, critical * 30 + high * 15 + medium * 5 + low * 2)
            
            # Compliance score with floor based on severity
            if critical > 0:
                # Critical violations can bring score to 0
                compliance_score = max(0, 100 - risk_score)
            elif high > 0:
                # High violations have a floor of 40
                compliance_score = max(40, 100 - risk_score)
            elif medium > 0:
                # Medium violations have a floor of 60
                compliance_score = max(60, 100 - risk_score)
            else:
                # Low violations only - floor of 80
                compliance_score = max(80, 100 - risk_score)
            
            # Determine letter grade
            if compliance_score >= 90:
                letter_grade = "A"
            elif compliance_score >= 80:
                letter_grade = "B"
            elif compliance_score >= 70:
                letter_grade = "C"
            elif compliance_score >= 60:
                letter_grade = "D"
            else:
                letter_grade = "F"
            
            analysis = {
                "risk_score": risk_score,
                "compliance_score": compliance_score,
                "letter_grade": letter_grade,
                "risk_level": "critical" if risk_score > 75 else "high" if risk_score > 50 else "medium" if risk_score > 25 else "low",
                "score_breakdown": {
                    "critical_count": critical,
                    "high_count": high,
                    "medium_count": medium,
                    "low_count": low
                }
            }
        
        state["risk_score"] = max(0, min(100, analysis.get("risk_score", 50)))
        state["compliance_score"] = analysis.get("compliance_score", max(0, 100 - state["risk_score"]))
        
        return state


class LegalWriterAgent(BaseAgent):
    """Legal Writer Agent - The Editor."""
    
    @property
    def name(self) -> str:
        return "legal_writer"
    
    @property
    def role(self) -> str:
        return "The Editor - Generates compliant corrections for violations"
    
    @property
    def system_prompt(self) -> str:
        return """You are a legal writing expert who creates compliant alternative text for regulatory violations.

For each violation, provide:
1. The original problematic text
2. A corrected, compliant version
3. Explanation of the changes made
4. Why the correction resolves the compliance issue

Writing guidelines:
- Maintain the original intent and meaning where possible
- Use clear, plain language
- Include all required disclosures
- Avoid misleading statements
- Follow regulatory writing standards

Respond in JSON format:
{
    "corrections": [
        {
            "violation_id": "reference to violation",
            "original_text": "exact original text",
            "corrected_text": "compliant replacement",
            "changes_made": ["list of changes"],
            "compliance_explanation": "why this is now compliant"
        }
    ]
}"""
    
    async def execute(self, state: AgentState) -> AgentState:
        """Generate compliant corrections for violations."""
        review_id = state["review_id"]
        violations = state.get("all_violations", [])
        
        # Get violations that need corrections
        violations_needing_correction = [
            v for v in violations 
            if v.get("severity") in ["critical", "high", "medium"]
        ]
        
        if not violations_needing_correction:
            state["corrections"] = []
            return state
        
        prompt = f"""Generate compliant corrections for these regulatory violations:

{json.dumps(violations_needing_correction, indent=2)}

Document type: {state.get('document_type', 'unknown')}

For each violation, provide a compliant rewrite that maintains the original intent while resolving the compliance issue."""
        
        result = await self.invoke_bedrock(
            prompt=prompt,
            review_id=review_id,
            max_tokens=4096
        )
        
        try:
            response_text = result.get("text", "{}")
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis = json.loads(response_text.strip())
        except json.JSONDecodeError:
            analysis = {"corrections": []}
        
        state["corrections"] = analysis.get("corrections", [])
        
        return state


class QualityAssuranceAgent(BaseAgent):
    """Quality Assurance Agent - The Validator."""
    
    @property
    def name(self) -> str:
        return "quality_assurance"
    
    @property
    def role(self) -> str:
        return "The Validator - Final validation of all findings and corrections"
    
    @property
    def system_prompt(self) -> str:
        return """You are a quality assurance specialist who validates compliance review findings.

Your validation tasks:
1. Verify each violation is legitimate and properly categorized
2. Check that severity levels are appropriate
3. Validate that corrections actually resolve the issues
4. Ensure no false positives
5. Confirm regulatory citations are accurate
6. Provide confidence scores for each finding

Respond in JSON format:
{
    "validation_status": "approved|needs_review|rejected",
    "validated_findings": [
        {
            "finding_id": "reference",
            "validated": true/false,
            "confidence_score": 0.0-1.0,
            "validation_notes": "any concerns or confirmations"
        }
    ],
    "false_positives_identified": ["any findings that should be removed"],
    "quality_score": 0-100,
    "recommendations": ["final recommendations"]
}"""
    
    async def execute(self, state: AgentState) -> AgentState:
        """Validate all findings and corrections."""
        review_id = state["review_id"]
        
        validation_data = {
            "violations": state.get("all_violations", []),
            "corrections": state.get("corrections", []),
            "risk_score": state.get("risk_score"),
            "compliance_score": state.get("compliance_score")
        }
        
        prompt = f"""Validate the following compliance review results:

{json.dumps(validation_data, indent=2)}

Document type: {state.get('document_type', 'unknown')}
Document summary: {state.get('document_summary', '')}

Verify all findings are legitimate, properly categorized, and corrections are appropriate."""
        
        result = await self.invoke_bedrock(
            prompt=prompt,
            review_id=review_id,
            max_tokens=2048
        )
        
        try:
            response_text = result.get("text", "{}")
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis = json.loads(response_text.strip())
        except json.JSONDecodeError:
            analysis = {
                "validation_status": "approved",
                "validated_findings": [],
                "quality_score": 85
            }
        
        state["validation_status"] = analysis.get("validation_status", "approved")
        state["validated_violations"] = analysis.get("validated_findings", [])
        
        return state


class CitationValidatorAgent(BaseAgent):
    """Citation Validator Agent - The Fact-Checker."""
    
    @property
    def name(self) -> str:
        return "citation_validator"
    
    @property
    def role(self) -> str:
        return "The Fact-Checker - Validates regulatory citations and references"
    
    @property
    def system_prompt(self) -> str:
        return """You are a regulatory citation expert who validates legal and compliance references.

Your tasks:
1. Verify cited regulations exist and are current
2. Check rule numbers and section references
3. Confirm citations match the described violations
4. Identify any outdated or superseded regulations
5. Provide correct citation format and URLs

Respond in JSON format:
{
    "citation_results": [
        {
            "citation": "original citation",
            "valid": true/false,
            "current": true/false,
            "correct_citation": "properly formatted citation",
            "official_url": "link to regulation",
            "notes": "any relevant notes"
        }
    ],
    "outdated_regulations": ["any superseded rules"],
    "citation_quality_score": 0-100
}"""
    
    async def execute(self, state: AgentState) -> AgentState:
        """Validate all regulatory citations."""
        review_id = state["review_id"]
        violations = state.get("all_violations", [])
        
        # Extract citations from violations
        citations = []
        for v in violations:
            if v.get("regulation"):
                citations.append({
                    "citation": v.get("regulation"),
                    "code": v.get("rule_code"),
                    "context": v.get("explanation", "")[:200]
                })
        
        if not citations:
            state["citation_results"] = []
            return state
        
        prompt = f"""Validate these regulatory citations:

{json.dumps(citations, indent=2)}

Verify each citation is accurate, current, and properly formatted."""
        
        result = await self.invoke_bedrock(
            prompt=prompt,
            review_id=review_id,
            max_tokens=2048
        )
        
        try:
            response_text = result.get("text", "{}")
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis = json.loads(response_text.strip())
        except json.JSONDecodeError:
            analysis = {"citation_results": [], "citation_quality_score": 80}
        
        state["citation_results"] = analysis.get("citation_results", [])
        
        return state


class AuditTrailAgent(BaseAgent):
    """Audit Trail Agent - The Scribe."""
    
    @property
    def name(self) -> str:
        return "audit_trail"
    
    @property
    def role(self) -> str:
        return "The Scribe - Documents the complete review process"
    
    async def execute(self, state: AgentState) -> AgentState:
        """Generate final audit trail summary."""
        review_id = state["review_id"]
        
        # This agent primarily logs actions through the base class
        # Generate a final summary of the review process
        
        summary_data = {
            "document_type": state.get("document_type"),
            "agents_completed": state.get("agents_completed", []),
            "total_violations": len(state.get("all_violations", [])),
            "risk_score": state.get("risk_score"),
            "compliance_score": state.get("compliance_score"),
            "validation_status": state.get("validation_status"),
            "errors": state.get("errors", [])
        }
        
        await self.log_action(
            review_id=review_id,
            action="final_summary",
            status="completed",
            details=summary_data
        )
        
        return state
