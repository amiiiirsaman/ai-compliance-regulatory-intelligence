# Agent Specifications: Compliance & Regulatory Intelligence System

**Version:** 1.0  
**Date:** 2026-01-31

---

## 1. Introduction

This document provides detailed specifications for each of the 12 specialized AI agents in the Compliance & Regulatory Intelligence System. Each agent is an expert in its domain, contributing to a comprehensive and robust compliance review process.

---

## 2. Core AI Agent Architecture

All 12 specialized AI agents are built on a common architecture:

- **Framework:** LangChain & LangGraph
- **LLM:** AWS Bedrock (Nova Pro)
- **Knowledge Source:** A combination of real-time data APIs, internal regulatory databases, and web scraping for updates.
- **Tools:** Each agent has a set of specific tools (e.g., API calls to regulatory databases, internal calculation functions) to perform its tasks.

### Standard Agent Prompt Structure

Each agent is initialized with a system prompt that defines its persona, role, and constraints. The prompt follows this template:

```
You are [Agent Name], a world-class [Agent Role] for a leading financial institution. Your persona is [Persona Description: e.g., meticulous, analytical, and authoritative].

Your primary responsibilities are:
- [Responsibility 1]
- [Responsibility 2]

Your analysis must be objective and based solely on the data provided. You must output your analysis in a structured JSON format.

Begin!
```

---

## 3. AI Agent Specifications

### 1. Document Reviewer Agent

- **Role:** The Analyst
- **Description:** Performs the initial analysis of the uploaded document.
- **Tools:**
    - `extract_text_with_textract(document_path)`
    - `identify_document_type(text)`
- **Output:** A JSON object with the document type, a summary of the content, and a list of potential risk areas.

### 2. Regulatory Expert Agent

- **Role:** The Coordinator
- **Description:** Aggregates and synthesizes findings from all specialist agents.
- **Tools:** None. It is a pure reasoning agent.
- **Output:** A JSON object with a consolidated list of all identified violations, ranked by severity.

### 3. Legal Writer Agent

- **Role:** The Editor
- **Description:** Generates compliant alternatives for non-compliant text.
- **Tools:** None. It is a pure reasoning agent.
- **Output:** A JSON object for each violation with the original text, the corrected text, and an explanation of the changes.

### 4. Quality Assurance Agent

- **Role:** The Validator
- **Description:** Performs a final review of the entire compliance analysis.
- **Tools:** None. It is a pure reasoning agent.
- **Output:** A JSON object with a final validation status (Approved/Rejected), a confidence score, and an audit-ready confirmation.

### 5. FINRA Specialist Agent

- **Role:** The FINRA Expert
- **Description:** Specializes in the rules and regulations of the Financial Industry Regulatory Authority.
- **Tools:**
    - `query_finra_database(rule_number)`
- **Output:** A JSON object listing any identified FINRA violations with specific rule citations.

### 6. SEC Specialist Agent

- **Role:** The SEC Expert
- **Description:** Specializes in the regulations of the U.S. Securities and Exchange Commission.
- **Tools:**
    - `query_sec_database(regulation_name)`
- **Output:** A JSON object listing any identified SEC violations with specific rule citations.

### 7. CFPB Specialist Agent

- **Role:** The Consumer Advocate
- **Description:** Specializes in consumer protection regulations from the Consumer Financial Protection Bureau.
- **Tools:**
    - `query_cfpb_database(regulation_name)`
- **Output:** A JSON object listing any identified CFPB violations with specific rule citations.

### 8. AML/KYC Agent

- **Role:** The Gatekeeper
- **Description:** Focuses on Anti-Money Laundering and Know-Your-Customer regulations.
- **Tools:**
    - `check_for_aml_red_flags(text)`
- **Output:** A JSON object identifying any potential AML/KYC issues.

### 9. Data Privacy Agent

- **Role:** The Guardian
- **Description:** Ensures compliance with data privacy laws like GDPR and CCPA.
- **Tools:**
    - `scan_for_pii(text)`
    - `check_privacy_policy_compliance(text)`
- **Output:** A JSON object listing any data privacy violations.

### 10. Risk Assessment Agent

- **Role:** The Scorer
- **Description:** Quantifies the risk associated with each compliance violation.
- **Tools:**
    - `calculate_risk_score(violation_details)`
- **Output:** A JSON object for each violation with a risk score (1-100) and a severity level (Low, Medium, High, Critical).

### 11. Audit Trail Agent

- **Role:** The Scribe
- **Description:** Creates a detailed, immutable log of the entire compliance review process.
- **Tools:**
    - `log_agent_action(agent_name, action, timestamp)`
- **Output:** A structured log file in JSON format.

### 12. Citation Validator Agent

- **Role:** The Fact-Checker
- **Description:** Verifies the accuracy and relevance of all regulatory citations.
- **Tools:**
    - `verify_citation(citation)`
- **Output:** A JSON object confirming the validity of each citation and providing a link to the source.
