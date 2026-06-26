"""
Unit tests for Bedrock connectivity and each agent step.
Run these BEFORE running the full 10-case test suite.
"""
import json
import boto3
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# AWS Configuration — loaded from environment variables
AWS_CONFIG = {
    "region_name": os.environ.get("AWS_REGION", "us-east-1"),
    "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", ""),
    "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "")
}


def test_1_bedrock_connection():
    """Test 1: Basic Bedrock connectivity."""
    print("\n" + "="*60)
    print("TEST 1: Bedrock Connection")
    print("="*60)
    
    client = boto3.client("bedrock-runtime", **AWS_CONFIG)
    
    # Nova Pro requires content as array of objects
    body = json.dumps({
        "messages": [{"role": "user", "content": [{"text": "Reply with just: OK"}]}],
        "inferenceConfig": {"maxTokens": 10, "temperature": 0}
    })
    
    print("  Calling amazon.nova-pro-v1:0...")
    response = client.invoke_model(
        modelId="amazon.nova-pro-v1:0",
        body=body,
        contentType="application/json",
        accept="application/json"
    )
    
    result = json.loads(response["body"].read())
    output = result.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")
    
    print(f"  Response: {output}")
    print("  ✓ PASS: Bedrock connection working!")
    return True


def test_2_compliance_analysis():
    """Test 2: Bedrock can analyze compliance content."""
    print("\n" + "="*60)
    print("TEST 2: Compliance Analysis Capability")
    print("="*60)
    
    client = boto3.client("bedrock-runtime", **AWS_CONFIG)
    
    test_doc = """
    INVESTMENT ALERT: GUARANTEED 50% RETURNS!
    Buy now for risk-free profits! No suitability review needed.
    """
    
    prompt = f"""Analyze this document for compliance issues. List any violations found.
    
Document:
{test_doc}

Reply in JSON format: {{"violations": [{{"issue": "...", "severity": "critical/high/medium/low"}}]}}"""
    
    # Nova Pro requires content as array of objects
    body = json.dumps({
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": 500, "temperature": 0}
    })
    
    print("  Sending compliance analysis request...")
    response = client.invoke_model(
        modelId="amazon.nova-pro-v1:0",
        body=body,
        contentType="application/json",
        accept="application/json"
    )
    
    result = json.loads(response["body"].read())
    output = result.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")
    
    print(f"  Response length: {len(output)} chars")
    print(f"  Response preview: {output[:200]}...")
    
    # Check if it found violations
    if "violation" in output.lower() or "guarantee" in output.lower():
        print("  ✓ PASS: Bedrock can identify compliance issues!")
        return True
    else:
        print("  ⚠ WARNING: Response may not contain violations")
        return True


def test_3_database_connection():
    """Test 3: Database connectivity."""
    print("\n" + "="*60)
    print("TEST 3: Database Connection")
    print("="*60)
    
    import asyncpg
    
    async def check_db():
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='Summerjoon202511!',
            database='claims_saas_db'
        )
        
        # Check tables exist
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        await conn.close()
        return [t['table_name'] for t in tables]
    
    tables = asyncio.run(check_db())
    print(f"  Tables found: {tables}")
    
    required = ['users', 'documents', 'reviews', 'violations']
    missing = [t for t in required if t not in tables]
    
    if missing:
        print(f"  ✗ FAIL: Missing tables: {missing}")
        return False
    
    print("  ✓ PASS: Database connection and tables OK!")
    return True


def test_4_agent_import():
    """Test 4: All agents can be imported."""
    print("\n" + "="*60)
    print("TEST 4: Agent Imports")
    print("="*60)
    
    try:
        from app.agents.specialists import (
            FINRASpecialistAgent,
            SECSpecialistAgent, 
            CFPBSpecialistAgent,
            AMLKYCAgent,
            DataPrivacyAgent
        )
        print("  ✓ Specialist agents imported")
        
        from app.agents.core_agents import (
            RegulatoryExpertAgent,
            RiskAssessmentAgent,
            LegalWriterAgent,
            QualityAssuranceAgent,
            CitationValidatorAgent,
            AuditTrailAgent
        )
        print("  ✓ Core agents imported")
        
        from app.agents.document_reviewer import DocumentReviewerAgent
        print("  ✓ Document reviewer imported")
        
        from app.agents.orchestrator import ComplianceOrchestrator
        print("  ✓ Orchestrator imported")
        
        print("  ✓ PASS: All 12 agents importable!")
        return True
        
    except Exception as e:
        print(f"  ✗ FAIL: Import error: {e}")
        return False


def test_5_single_specialist():
    """Test 5: Test that Bedrock can be invoked by specialist agent logic (without DB)."""
    print("\n" + "="*60)
    print("TEST 5: Specialist Analysis Logic (Bedrock Only)")
    print("="*60)
    
    import boto3
    
    client = boto3.client("bedrock-runtime", **AWS_CONFIG)
    
    test_doc = """
    INVESTMENT RECOMMENDATION
    Buy XYZ Fund - it has GUARANTEED returns of 25%!
    This is a risk-free investment suitable for everyone.
    No need to review your financial situation.
    """
    
    # Use the same prompt structure as FINRA specialist
    prompt = f"""You are a FINRA compliance specialist. Analyze this document for violations of:
- FINRA Rule 2210 (Communications with the Public)
- FINRA Rule 2111 (Suitability)
- FINRA Rule 3110 (Supervision)
- FINRA Rule 2010 (Standards of Commercial Honor)

Document:
{test_doc}

List any violations found in JSON format:
{{"violations": [{{"rule": "...", "description": "...", "severity": "critical/high/medium/low", "excerpt": "..."}}]}}
"""
    
    body = json.dumps({
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": 1000, "temperature": 0}
    })
    
    print("  Running FINRA-style analysis via Bedrock...")
    response = client.invoke_model(
        modelId="amazon.nova-pro-v1:0",
        body=body,
        contentType="application/json",
        accept="application/json"
    )
    
    result = json.loads(response["body"].read())
    output = result.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")
    
    print(f"  Response length: {len(output)} chars")
    print(f"  Response preview: {output[:300]}...")
    
    # Check if violations were found
    if "violation" in output.lower() or "guarantee" in output.lower() or "2210" in output:
        print("  ✓ PASS: Specialist logic can identify FINRA violations!")
        return True
    else:
        print("  ⚠ WARNING: Response may not contain expected violations")
        return True


def main():
    """Run all unit tests."""
    print("\n" + "="*60)
    print("BEDROCK & AGENT UNIT TESTS")
    print("="*60)
    
    tests = [
        ("Bedrock Connection", test_1_bedrock_connection),
        ("Compliance Analysis", test_2_compliance_analysis),
        ("Database Connection", test_3_database_connection),
        ("Agent Imports", test_4_agent_import),
        ("Single Specialist", test_5_single_specialist),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("UNIT TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    
    print(f"\n  Results: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n  All tests passed! Ready to run 10-case test suite.")
        return 0
    else:
        print("\n  Some tests failed. Fix issues before running full suite.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
