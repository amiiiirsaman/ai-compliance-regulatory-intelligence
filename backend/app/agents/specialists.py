"""Regulatory Specialist Agents - FINRA, SEC, CFPB, AML/KYC, Data Privacy."""
import json
from typing import Any, Dict, List

from .base import BaseAgent, AgentState


class FINRASpecialistAgent(BaseAgent):
    """FINRA Specialist Agent - The FINRA Expert."""
    
    @property
    def name(self) -> str:
        return "finra_specialist"
    
    @property
    def role(self) -> str:
        return "The FINRA Expert - Specialist in FINRA regulations and compliance"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert in FINRA (Financial Industry Regulatory Authority) regulations.
Your specialty includes:
- Rule 2210: Communications with the Public
- Rule 2111: Suitability
- Rule 3110: Supervision
- Rule 2010: Standards of Commercial Honor
- Rule 4512: Customer Account Information

Analyze documents for FINRA compliance violations. For each violation found, provide:
- Specific rule violated
- Exact text that violates the rule
- Explanation of why it's a violation
- Severity level (critical, high, medium, low)
- Suggested correction

Respond in JSON format:
{
    "findings": [
        {
            "rule": "FINRA Rule XXXX",
            "rule_code": "2210(d)(1)(A)",
            "violated_text": "exact text from document",
            "explanation": "why this violates the rule",
            "severity": "critical|high|medium|low",
            "suggested_correction": "compliant alternative text",
            "citation_url": "https://www.finra.org/..."
        }
    ],
    "compliant_areas": ["list of areas that are compliant"],
    "overall_assessment": "summary of FINRA compliance status"
}"""
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute FINRA compliance analysis."""
        review_id = state["review_id"]
        document_text = state.get("document_text", "")[:40000]
        document_type = state.get("document_type", "unknown")
        risk_areas = state.get("risk_areas", [])
        
        prompt = f"""Analyze this {document_type} document for FINRA compliance violations.

Focus areas based on initial analysis: {', '.join(risk_areas) if risk_areas else 'General review'}

Document content:
---
{document_text}
---

Identify all FINRA rule violations with specific citations."""
        
        result = await self.invoke_bedrock(
            prompt=prompt,
            review_id=review_id,
            max_tokens=4096
        )
        
        # Parse response
        try:
            response_text = result.get("text", "{}")
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            analysis = json.loads(response_text.strip())
        except json.JSONDecodeError:
            analysis = {"findings": [], "compliant_areas": [], "overall_assessment": ""}
        
        # Save findings to state
        state["finra_findings"] = analysis.get("findings", [])
        
        # Save violations to database
        for finding in analysis.get("findings", []):
            await self.save_violation(
                review_id=review_id,
                regulation=finding.get("rule", "FINRA Rule"),
                regulation_code=finding.get("rule_code"),
                severity=finding.get("severity", "medium"),
                explanation=finding.get("explanation", ""),
                original_text=finding.get("violated_text"),
                corrected_text=finding.get("suggested_correction"),
                citation_url=finding.get("citation_url")
            )
        
        return state


class SECSpecialistAgent(BaseAgent):
    """SEC Specialist Agent - The SEC Expert."""
    
    @property
    def name(self) -> str:
        return "sec_specialist"
    
    @property
    def role(self) -> str:
        return "The SEC Expert - Specialist in SEC regulations and securities law"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert in SEC (Securities and Exchange Commission) regulations.
Your specialty includes:
- Rule 156: Investment Company Sales Literature
- Regulation S-P: Privacy of Consumer Financial Information
- Regulation Best Interest (Reg BI)
- Rule 10b-5: Anti-Fraud Provisions
- Form ADV Requirements

Analyze documents for SEC compliance violations. For each violation found, provide:
- Specific rule or regulation violated
- Exact text that violates the rule
- Explanation of why it's a violation
- Severity level
- Suggested correction

Respond in JSON format:
{
    "findings": [
        {
            "rule": "SEC Rule/Regulation",
            "rule_code": "156(b)(1)",
            "violated_text": "exact text from document",
            "explanation": "why this violates the rule",
            "severity": "critical|high|medium|low",
            "suggested_correction": "compliant alternative text",
            "citation_url": "https://www.sec.gov/..."
        }
    ],
    "compliant_areas": ["list of areas that are compliant"],
    "overall_assessment": "summary of SEC compliance status"
}"""
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute SEC compliance analysis."""
        review_id = state["review_id"]
        document_text = state.get("document_text", "")[:40000]
        document_type = state.get("document_type", "unknown")
        
        prompt = f"""Analyze this {document_type} document for SEC compliance violations.

Document content:
---
{document_text}
---

Identify all SEC rule and regulation violations with specific citations."""
        
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
            analysis = {"findings": [], "compliant_areas": [], "overall_assessment": ""}
        
        state["sec_findings"] = analysis.get("findings", [])
        
        for finding in analysis.get("findings", []):
            await self.save_violation(
                review_id=review_id,
                regulation=finding.get("rule", "SEC Rule"),
                regulation_code=finding.get("rule_code"),
                severity=finding.get("severity", "medium"),
                explanation=finding.get("explanation", ""),
                original_text=finding.get("violated_text"),
                corrected_text=finding.get("suggested_correction"),
                citation_url=finding.get("citation_url")
            )
        
        return state


class CFPBSpecialistAgent(BaseAgent):
    """CFPB Specialist Agent - The Consumer Advocate."""
    
    @property
    def name(self) -> str:
        return "cfpb_specialist"
    
    @property
    def role(self) -> str:
        return "The Consumer Advocate - Specialist in CFPB regulations and consumer protection"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert in CFPB (Consumer Financial Protection Bureau) regulations.
Your specialty includes:
- TILA (Truth in Lending Act)
- RESPA (Real Estate Settlement Procedures Act)
- FCRA (Fair Credit Reporting Act)
- UDAAP (Unfair, Deceptive, or Abusive Acts or Practices)
- ECOA (Equal Credit Opportunity Act)

Analyze documents for CFPB compliance violations. For each violation found, provide:
- Specific regulation violated
- Exact text that violates the regulation
- Explanation of the consumer protection issue
- Severity level
- Suggested correction

Respond in JSON format:
{
    "findings": [
        {
            "rule": "CFPB Regulation/Act",
            "rule_code": "TILA Section X",
            "violated_text": "exact text from document",
            "explanation": "consumer protection issue",
            "severity": "critical|high|medium|low",
            "suggested_correction": "compliant alternative text",
            "citation_url": "https://www.consumerfinance.gov/..."
        }
    ],
    "compliant_areas": ["list of areas that are compliant"],
    "overall_assessment": "summary of CFPB compliance status"
}"""
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute CFPB compliance analysis."""
        review_id = state["review_id"]
        document_text = state.get("document_text", "")[:40000]
        document_type = state.get("document_type", "unknown")
        
        prompt = f"""Analyze this {document_type} document for CFPB compliance violations.

Document content:
---
{document_text}
---

Identify all CFPB regulation violations focusing on consumer protection."""
        
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
            analysis = {"findings": [], "compliant_areas": [], "overall_assessment": ""}
        
        state["cfpb_findings"] = analysis.get("findings", [])
        
        for finding in analysis.get("findings", []):
            await self.save_violation(
                review_id=review_id,
                regulation=finding.get("rule", "CFPB Regulation"),
                regulation_code=finding.get("rule_code"),
                severity=finding.get("severity", "medium"),
                explanation=finding.get("explanation", ""),
                original_text=finding.get("violated_text"),
                corrected_text=finding.get("suggested_correction"),
                citation_url=finding.get("citation_url")
            )
        
        return state


class AMLKYCAgent(BaseAgent):
    """AML/KYC Agent - The Gatekeeper."""
    
    @property
    def name(self) -> str:
        return "aml_kyc_agent"
    
    @property
    def role(self) -> str:
        return "The Gatekeeper - Specialist in AML/KYC compliance and suspicious activity detection"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert in AML (Anti-Money Laundering) and KYC (Know Your Customer) regulations.
Your specialty includes:
- Bank Secrecy Act (BSA)
- USA PATRIOT Act
- SAR (Suspicious Activity Report) requirements
- CDD (Customer Due Diligence) Rule
- FinCEN regulations

Analyze documents for AML/KYC compliance issues. Look for:
- Missing or inadequate customer identification procedures
- Lack of suspicious activity monitoring provisions
- Inadequate record-keeping requirements
- Missing beneficial ownership requirements
- Red flags for potential money laundering

Respond in JSON format:
{
    "findings": [
        {
            "rule": "AML/KYC Regulation",
            "rule_code": "BSA Section X",
            "violated_text": "exact text from document",
            "explanation": "AML/KYC compliance issue",
            "severity": "critical|high|medium|low",
            "suggested_correction": "compliant alternative text",
            "red_flag": true/false
        }
    ],
    "red_flags": ["list of potential money laundering red flags"],
    "overall_assessment": "summary of AML/KYC compliance status"
}"""
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute AML/KYC compliance analysis."""
        review_id = state["review_id"]
        document_text = state.get("document_text", "")[:40000]
        document_type = state.get("document_type", "unknown")
        
        prompt = f"""Analyze this {document_type} document for AML/KYC compliance issues.

Document content:
---
{document_text}
---

Identify all AML/KYC compliance issues and potential red flags."""
        
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
            analysis = {"findings": [], "red_flags": [], "overall_assessment": ""}
        
        state["aml_findings"] = analysis.get("findings", [])
        
        for finding in analysis.get("findings", []):
            await self.save_violation(
                review_id=review_id,
                regulation=finding.get("rule", "AML/KYC Regulation"),
                regulation_code=finding.get("rule_code"),
                severity=finding.get("severity", "high"),  # AML issues default to high
                explanation=finding.get("explanation", ""),
                original_text=finding.get("violated_text"),
                corrected_text=finding.get("suggested_correction")
            )
        
        return state


class DataPrivacyAgent(BaseAgent):
    """Data Privacy Agent - The Guardian."""
    
    @property
    def name(self) -> str:
        return "data_privacy_agent"
    
    @property
    def role(self) -> str:
        return "The Guardian - Specialist in data privacy regulations and PII protection"
    
    @property
    def system_prompt(self) -> str:
        return """You are an expert in data privacy regulations and PII (Personally Identifiable Information) protection.
Your specialty includes:
- GDPR (General Data Protection Regulation)
- CCPA (California Consumer Privacy Act)
- HIPAA (Health Insurance Portability and Accountability Act)
- GLBA (Gramm-Leach-Bliley Act) Privacy Rule
- State privacy laws

Analyze documents for data privacy compliance. Look for:
- Inadequate privacy notices or disclosures
- Missing data subject rights information
- Improper data sharing provisions
- Lack of consent mechanisms
- Insufficient data security provisions
- PII exposure or handling issues

Respond in JSON format:
{
    "findings": [
        {
            "rule": "Privacy Regulation",
            "rule_code": "GDPR Article X",
            "violated_text": "exact text from document",
            "explanation": "privacy compliance issue",
            "severity": "critical|high|medium|low",
            "suggested_correction": "compliant alternative text",
            "pii_risk": true/false
        }
    ],
    "pii_detected": ["types of PII found in document"],
    "overall_assessment": "summary of data privacy compliance status"
}"""
    
    async def execute(self, state: AgentState) -> AgentState:
        """Execute data privacy compliance analysis."""
        review_id = state["review_id"]
        document_text = state.get("document_text", "")[:40000]
        document_type = state.get("document_type", "unknown")
        
        prompt = f"""Analyze this {document_type} document for data privacy compliance issues.

Document content:
---
{document_text}
---

Identify all data privacy compliance issues and PII handling concerns."""
        
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
            analysis = {"findings": [], "pii_detected": [], "overall_assessment": ""}
        
        state["privacy_findings"] = analysis.get("findings", [])
        
        for finding in analysis.get("findings", []):
            await self.save_violation(
                review_id=review_id,
                regulation=finding.get("rule", "Privacy Regulation"),
                regulation_code=finding.get("rule_code"),
                severity=finding.get("severity", "high"),  # Privacy issues default to high
                explanation=finding.get("explanation", ""),
                original_text=finding.get("violated_text"),
                corrected_text=finding.get("suggested_correction")
            )
        
        return state
