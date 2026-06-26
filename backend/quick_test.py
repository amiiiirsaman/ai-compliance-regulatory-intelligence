"""
Self-contained test script that runs 3 test cases sequentially.
Tests the compliance review pipeline end-to-end.
"""
import asyncio
import httpx
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001/api/v1"
TEST_USER = {"email": f"test{int(time.time())}@example.com", "password": "TestPass123!"}
TIMEOUT_SECONDS = 600

# 3 key test documents: Compliant, Medium, Severe
TEST_DOCS = {
    "compliant": """
WEALTH ADVISORY SERVICES - COMPREHENSIVE INVESTMENT RECOMMENDATION
Document ID: WAS-2026-001 | SEC File: 801-12345 | FINRA CRD: 123456

=== CLIENT PROFILE & SUITABILITY (FINRA Rule 2111 Compliance) ===
Client Name: John Smith | Account: 98765432
Risk Tolerance: Moderate (Assessed Score: 6/10)
Investment Objective: Long-term growth with capital preservation
Time Horizon: 10+ years until retirement
Annual Income: $150,000 | Net Worth: $500,000 | Liquid Assets: $200,000
Investment Experience: 5+ years in stocks and bonds
Client signed suitability questionnaire on file (dated 01/15/2026).

=== IDENTITY VERIFICATION (AML/BSA Compliance) ===
KYC completed and verified: ✓ Government-issued ID verified
Beneficial Ownership documented: ✓ Client is sole account holder
No suspicious activity indicators: ✓ Source of funds verified
CIP requirements satisfied per 31 CFR 1020.220

=== INVESTMENT RECOMMENDATION ===
Based on your suitability profile, we recommend:
- 70% Vanguard Total Stock Market Index (VTI) - Expense Ratio: 0.03%
- 30% Vanguard Total Bond Market Index (BND) - Expense Ratio: 0.03%
Total annual fee: 0.03% ($60 on $200,000)

=== RISK DISCLOSURE (SEC Regulation Best Interest) ===
IMPORTANT: All investments involve risk, including potential loss of principal.
- Past performance does not guarantee future results
- Market conditions can cause significant volatility
- Historical S&P 500 returns of 7-10% annually are not guaranteed
- Your investment value may fluctuate daily
We receive no additional compensation for this recommendation.
No conflicts of interest exist regarding this recommendation.

=== PRIVACY NOTICE (GLBA, CCPA, GDPR Compliance) ===
How we protect your information:
- We collect: name, SSN, address, financial information for account servicing
- We DO NOT sell your personal information to third parties
- We share information only as required by law or with your consent
- Security measures: AES-256 encryption, multi-factor authentication
Your CCPA Rights (California residents):
- Right to know what personal information we collect
- Right to delete your personal information
- Right to opt-out of sale (we do not sell data)
- Right to non-discrimination
Contact our Privacy Officer at privacy@example.com for requests.

=== CERTIFICATIONS ===
This document complies with:
✓ FINRA Rule 2111 (Suitability) ✓ FINRA Rule 2210 (Communications)
✓ SEC Regulation Best Interest ✓ SEC Rule 17a-4 (Recordkeeping)
✓ CFPB Consumer Protection ✓ Bank Secrecy Act/AML
✓ GLBA Privacy Requirements ✓ CCPA/CPRA Privacy Rights
Prepared by: Licensed Representative #12345 | Supervisor Reviewed: ✓
""",
    "medium_risk": """
INVESTMENT OPPORTUNITY - HIGH GROWTH FUND

This fund has consistently beaten the market!
Expected returns: 15-20% annually.

MINIMUM INVESTMENT: $10,000

FEES: 2.5% management fee, 20% performance fee

Note: While we attempt to follow industry guidelines, this is not personalized advice.
Past performance shown above. Consult your advisor.
""",
    "severe_violations": """
GUARANTEED INVESTMENT RETURNS!!!

🚀 GUARANTEED 50% RETURNS - NO RISK! 🚀

Why wait? Our proprietary algorithm GUARANTEES profits!
We've NEVER had a losing month!

SEND MONEY NOW to secure your spot!
Wire transfer to offshore account: XXXXX

NO DOCUMENTATION NEEDED - We don't ask questions!
Perfect for those wanting PRIVACY from regulators.

ACT NOW - Limited spots available!
""",
}

async def run_test():
    print("=" * 70)
    print("COMPLIANCE SYSTEM - 3 CASE TEST")
    print("=" * 70)
    print(f"Started: {datetime.now().isoformat()}")
    
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        # 1. Auth
        print("\n[1/4] Authenticating...")
        try:
            # Try to register first
            r = await client.post(f"{BASE_URL}/auth/register", json=TEST_USER)
            if r.status_code in [200, 201]:
                print(f"  → Registered new user")
            
            # Always login to get token
            r = await client.post(f"{BASE_URL}/auth/login", 
                data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
            token = r.json().get("access_token")
            if not token:
                print(f"  ERROR: No token - {r.text[:200]}")
                return
            headers = {"Authorization": f"Bearer {token}"}
            print(f"  ✓ Authenticated")
        except Exception as e:
            print(f"  ERROR: {e}")
            return

        results = []
        
        for idx, (name, content) in enumerate(TEST_DOCS.items(), 1):
            print(f"\n[{idx+1}/4] Testing: {name}")
            
            # Upload
            try:
                files = {"file": (f"{name}.txt", content, "text/plain")}
                r = await client.post(f"{BASE_URL}/documents/upload", files=files, headers=headers)
                data = r.json()
                doc_id = data.get("document_id")
                review_id = data.get("review_id")
                print(f"  → Uploaded: {doc_id} (review: {review_id})")
            except Exception as e:
                print(f"  ERROR uploading: {e}")
                continue
            
            # Poll for review completion
            try:
                print(f"  → Waiting for review to complete (may take 60-90s with sequential agents)...")
                start = time.time()
                max_wait = 600  # 10 minutes max - agents run sequentially
                last_status = None
                
                while time.time() - start < max_wait:
                    r = await client.get(f"{BASE_URL}/reviews/{review_id}", headers=headers)
                    if r.status_code != 200:
                        await asyncio.sleep(5)
                        continue
                    
                    data = r.json()
                    status = data.get("status", "")
                    
                    # Print status updates
                    if status != last_status:
                        elapsed = time.time() - start
                        print(f"    [{elapsed:.0f}s] Status: {status}")
                        last_status = status
                    
                    if status.upper() in ["COMPLETED", "COMPLETE"]:
                        elapsed = time.time() - start
                        score = data.get("compliance_score", 0)
                        violations = data.get("violations", [])
                        
                        # Count by severity
                        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
                        agents = set()
                        for v in violations:
                            sev = v.get("severity", "medium").lower()
                            counts[sev] = counts.get(sev, 0) + 1
                            agents.add(v.get("agent_source", "unknown"))
                        
                        print(f"  ✓ Score: {score}")
                        print(f"  ✓ Violations: {len(violations)} (C:{counts['critical']}, H:{counts['high']}, M:{counts['medium']}, L:{counts['low']})")
                        print(f"  ✓ Agents: {', '.join(sorted(agents)) or 'None'}")
                        print(f"  ✓ Time: {elapsed:.1f}s")
                        
                        results.append({
                            "name": name,
                            "score": score,
                            "violations": len(violations),
                            "counts": counts,
                            "agents": list(agents),
                            "time": elapsed
                        })
                        break
                    elif status == "FAILED":
                        print(f"  ERROR: Review failed - {data.get('error_message', 'Unknown error')}")
                        break
                    else:
                        # Still processing
                        await asyncio.sleep(5)
                else:
                    print(f"  ERROR: Timeout waiting for review completion")
                    
            except Exception as e:
                print(f"  ERROR reviewing: {e}")
                continue
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"{'Case':<20} {'Score':>8} {'Violations':>12} {'Agents':>8}")
        print("-" * 50)
        for r in results:
            print(f"{r['name']:<20} {r['score']:>8} {r['violations']:>12} {len(r['agents']):>8}")
        
        all_agents = set()
        for r in results:
            all_agents.update(r['agents'])
        print(f"\nTotal agents triggered: {len(all_agents)}")
        print(f"Agents: {', '.join(sorted(all_agents))}")
        
        # Check if scores decrease as expected
        if len(results) >= 3:
            if results[0]['score'] > results[1]['score'] > results[2]['score']:
                print("\n✓ PASS: Scores decrease as compliance worsens")
            else:
                print("\n⚠ WARNING: Scores may not follow expected pattern")
        
        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_test())
