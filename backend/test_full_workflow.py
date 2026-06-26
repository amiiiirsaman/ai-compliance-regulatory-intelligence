"""Test full compliance review workflow with proper analysis."""
import asyncio
import httpx
import time
import json

BASE_URL = "http://localhost:8001"

# Test document with MANY clear compliance violations across ALL regulation areas
TEST_DOCUMENT = """
PREMIER WEALTH ADVISORS - CLIENT COMMUNICATION
===============================================
Date: January 20, 2026
Client: Robert Williams (Account #PWA-2026-99182)
Advisor: Jennifer Martinez (Registration: EXPIRED)
Supervisor Review: NOT REQUIRED

=== INVESTMENT RECOMMENDATION ===

Dear Mr. Williams,

I am reaching out with URGENT news about an investment opportunity that 
will GUARANTEE you 40% returns with ZERO RISK. This is the safest 
investment available - you absolutely cannot lose money under any 
market conditions.

Based on CONFIDENTIAL INSIDER INFORMATION from my contact at MegaCorp 
Industries, their stock will triple in value next month when they 
announce their secret acquisition of TechStart Inc. I strongly 
recommend you move ALL of your retirement funds into MegaCorp stock 
immediately - this opportunity won't last!

=== TRANSACTION INSTRUCTIONS ===

IMPORTANT: You must act within 24 hours. To circumvent normal 
processing delays, please send funds via wire transfer:

Transaction Schedule (structured to avoid reporting thresholds):
- January 21: Wire $9,900 to Account 4521-8877-3345 (Cayman Islands)
- January 22: Wire $9,900 to Account 4521-8877-3346 (Cayman Islands)
- January 23: Wire $9,900 to Account 4521-8877-3347 (Cayman Islands)
- January 24: Wire $9,900 to Account 4521-8877-3348 (Cayman Islands)
- January 25: Wire $9,900 to Account 4521-8877-3349 (Cayman Islands)

=== CUSTOMER DUE DILIGENCE STATUS ===

The following items are WAIVED per my authority:
- Identity Verification: SKIPPED
- Source of Funds Documentation: NOT COLLECTED
- Beneficial Owner Identification: NOT REQUIRED
- Risk Assessment: BYPASSED (high-net-worth client exemption)
- Suspicious Activity Review: MANAGER OVERRIDE APPLIED

=== CLIENT PERSONAL DATA (UNENCRYPTED) ===

Full Name: Robert J. Williams
SSN: 456-78-9012
Date of Birth: November 23, 1962
Driver's License: CA D1234567
Mother's Maiden Name: Anderson
Bank Account: Chase ****7892, Routing 021000021
Credit Card: Amex 3782 822463 10005, CVV 4532, Exp 08/28
Home Address: 1234 Oak Street, Los Angeles, CA 90210
Email: robert.williams@email.com
Phone: (310) 555-0147

=== CONSUMER PROTECTION NOTICE ===

IMPORTANT DISCLOSURES:
- Past performance GUARANTEES future results
- You WILL make money with this investment
- This product is suitable for ALL investors
- There are NO fees associated with this recommendation
- You have NO right to cancel this transaction
- We are NOT required to act in your best interest
- Complaints should be directed to /dev/null

=== FAIR LENDING STATEMENT ===

Credit decisions were made based on the following factors:
- Applicant's neighborhood demographics
- Religious affiliation (determined from name analysis)
- Estimated ethnicity based on surname
- Age of applicant (over 60, higher risk category)

=== DATA HANDLING PRACTICES ===

Your personal information will be:
- Shared with unlimited third-party marketing partners
- Stored indefinitely with no deletion option
- Sold to data brokers without consent
- Transmitted unencrypted via email and fax
- Retained on unprotected backup drives
- Accessible to all company employees

No opt-out is available. Your continued relationship constitutes consent.

=== SIGNATURES ===

_________________________________
Jennifer Martinez
Financial Advisor (License EXPIRED 2024)
Premier Wealth Advisors

This document has NOT been reviewed by compliance.
This firm is NOT registered with SEC, FINRA, or state regulators.
"""


async def main():
    print("=" * 70)
    print("COMPLIANCE REVIEW WORKFLOW TEST")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Step 1: Register/Login
        print("\n📋 Step 1: Authentication")
        print("-" * 50)
        
        email = f"compliance_test_{int(time.time())}@example.com"
        
        reg_response = await client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
                "full_name": "Compliance Tester"
            }
        )
        
        if reg_response.status_code == 201:
            print(f"✓ Registered new user: {email}")
        elif reg_response.status_code == 400:
            print(f"→ User exists, logging in...")
        else:
            print(f"✗ Registration failed: {reg_response.text}")
            return
        
        # Login
        login_response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": email, "password": "TestPassword123!"}
        )
        
        if login_response.status_code != 200:
            print(f"✗ Login failed: {login_response.text}")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✓ Logged in successfully")
        
        # Step 2: Upload Document
        print("\n📤 Step 2: Document Upload")
        print("-" * 50)
        
        files = {
            "file": ("compliance_test_violations.txt", TEST_DOCUMENT.encode(), "text/plain")
        }
        
        upload_response = await client.post(
            f"{BASE_URL}/api/v1/documents/upload",
            headers=headers,
            files=files
        )
        
        if upload_response.status_code != 202:
            print(f"✗ Upload failed: {upload_response.text}")
            return
        
        upload_data = upload_response.json()
        document_id = upload_data["document_id"]
        review_id = upload_data["review_id"]
        
        print(f"✓ Document uploaded")
        print(f"  Document ID: {document_id}")
        print(f"  Review ID: {review_id}")
        
        # Step 3: Poll for review completion
        print("\n⏳ Step 3: Waiting for Review Completion")
        print("-" * 50)
        
        max_wait = 180  # 3 minutes max
        poll_interval = 5
        elapsed = 0
        
        while elapsed < max_wait:
            review_response = await client.get(
                f"{BASE_URL}/api/v1/reviews/{review_id}",
                headers=headers
            )
            
            if review_response.status_code != 200:
                print(f"  ⚠️ Failed to get review status: {review_response.status_code}")
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                continue
            
            review_data = review_response.json()
            status = review_data.get("status", "unknown")
            
            print(f"  [{elapsed}s] Status: {status}")
            
            if status == "complete":
                print(f"\n✓ Review completed!")
                break
            elif status == "failed":
                print(f"\n✗ Review failed!")
                error = review_data.get("error_message", "Unknown error")
                print(f"  Error: {error}")
                break
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        if elapsed >= max_wait:
            print(f"\n⚠️ Review timed out after {max_wait}s")
        
        # Step 4: Get Review Results
        print("\n📊 Step 4: Review Results")
        print("-" * 50)
        
        review_response = await client.get(
            f"{BASE_URL}/api/v1/reviews/{review_id}",
            headers=headers
        )
        
        if review_response.status_code == 200:
            review_data = review_response.json()
            
            print(f"  Status: {review_data.get('status')}")
            print(f"  Compliance Score: {review_data.get('compliance_score', 'N/A')}")
            print(f"  Risk Score: {review_data.get('risk_score', 'N/A')}")
            
            violations = review_data.get("violations", [])
            print(f"  Violations Found: {len(violations)}")
            
            if violations:
                print("\n  📋 Violations Detail:")
                for i, v in enumerate(violations, 1):
                    print(f"\n  [{i}] {v.get('regulation', 'Unknown')}")
                    print(f"      Severity: {v.get('severity', 'N/A')}")
                    print(f"      Agent: {v.get('agent_source', 'N/A')}")
                    explanation = v.get('explanation', '')[:200]
                    print(f"      Explanation: {explanation}...")
        else:
            print(f"✗ Failed to get results: {review_response.text}")
        
        # Step 5: Check Bedrock Logs
        print("\n📝 Step 5: Bedrock API Calls")
        print("-" * 50)
        
        try:
            logs_response = await client.get(
                f"{BASE_URL}/api/v1/reviews/{review_id}/bedrock-logs",
                headers=headers
            )
            
            if logs_response.status_code == 200:
                logs = logs_response.json()
                print(f"  Total Bedrock Calls: {len(logs)}")
                
                for log in logs[:5]:  # Show first 5
                    print(f"  • {log.get('agent_name')}: {log.get('latency_ms', 0)}ms, {log.get('input_tokens', 0)} in / {log.get('output_tokens', 0)} out")
            else:
                print(f"  Could not retrieve logs: {logs_response.status_code}")
        except Exception as e:
            print(f"  Error getting logs: {e}")
        
        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
