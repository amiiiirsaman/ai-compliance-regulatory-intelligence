"""
Compliance Test Suite - 10 Graduated Test Cases
Tests the full compliance review pipeline with documents ranging from 
perfectly compliant (Case 1) to catastrophically non-compliant (Case 10).

Scoring Formula:
- risk_score = min(100, critical*25 + high*15 + medium*8 + low*3)
- compliance_score = max(0, 100 - risk_score)

Target Scores:
- Case 1: ~100 (Model Compliant)
- Case 2: ~90 (Minor Issues) 
- Case 3: ~80 (Mostly Compliant)
- Case 4: ~65 (Mixed Compliance)
- Case 5: ~50 (Below Average)
- Case 6: ~40 (Problematic)
- Case 7: ~25 (Serious Violations)
- Case 8: ~15 (Major Non-Compliance)
- Case 9: ~5 (Severe Violations)
- Case 10: ~0 (Catastrophic)
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

BASE_URL = "http://127.0.0.1:8001/api/v1"
TEST_USER = {"email": "testcases@example.com", "password": "TestPass123!"}
TIMEOUT_SECONDS = 180  # 3 minutes max per test

# =============================================================================
# TEST DOCUMENTS - 10 GRADUATED CASES
# =============================================================================

TEST_DOCUMENTS = {
    # -------------------------------------------------------------------------
    # CASE 1: MODEL COMPLIANT (~100 score, 0 violations)
    # Perfect document following all regulations
    # -------------------------------------------------------------------------
    "case_01_model_compliant": """
WEALTH ADVISORY SERVICES - INVESTMENT RECOMMENDATION
Document ID: WAS-2026-001
Date: January 15, 2026
Client: John Smith (Account #12345678)

SUITABILITY ASSESSMENT COMPLETED:
This recommendation is based on comprehensive suitability analysis including:
- Client Risk Tolerance: Moderate (documented in Form CRS dated 01/10/2026)
- Investment Horizon: 10+ years retirement planning
- Annual Income: $150,000 | Net Worth: $850,000 (verified)
- Investment Objectives: Long-term growth with capital preservation

RECOMMENDED ALLOCATION:
- 60% Diversified Equity Index Funds (Expense Ratio: 0.03%)
- 30% Investment Grade Bond ETF (Duration: 5.2 years)
- 10% Money Market for liquidity

RISK DISCLOSURE (FINRA Rule 2210 & SEC Rule 156):
Past performance does not guarantee future results. All investments involve 
risk, including potential loss of principal. Market volatility may impact 
returns. This recommendation may not be suitable for all investors.

FEES AND COSTS DISCLOSURE (Reg BI Compliant):
- Advisory Fee: 0.50% annually, billed quarterly
- No transaction fees on recommended funds
- Total estimated annual cost: $4,250 on current portfolio

CONFLICTS OF INTEREST DISCLOSURE:
Our firm does not receive revenue sharing from any recommended funds.
Advisor compensation is fee-based only, not commission-based.

DATA PRIVACY NOTICE (GLBA/CCPA Compliant):
Your personal information is protected under our Privacy Policy dated 01/01/2026.
We do not sell your data. You may opt-out of marketing at any time.
Data retention: 7 years per regulatory requirements.

AML/KYC VERIFICATION COMPLETE:
- Identity verified via government-issued ID on 01/05/2026
- Address verified via utility bill
- Source of funds: Employment income (W-2 provided)
- No suspicious activity indicators identified

CLIENT ACKNOWLEDGMENT:
I have received, read, and understand this recommendation and all disclosures.
Signature: [Signed electronically by John Smith on 01/15/2026]

Prepared by: Licensed Advisor #CRD-123456
Supervisory Review: Completed by Principal #CRD-789012 on 01/15/2026
""",

    # -------------------------------------------------------------------------
    # CASE 2: MINOR ISSUES (~90 score, 1-2 low violations)
    # Nearly perfect but minor disclosure gaps
    # -------------------------------------------------------------------------
    "case_02_minor_issues": """
INVESTMENT ADVISORY COMMUNICATION
Date: January 20, 2026
Client: Sarah Johnson

PORTFOLIO RECOMMENDATION:
Based on our discussion of your financial goals, we recommend:
- 70% Growth Stock Fund (GROWX) - Excellent 5-year track record
- 20% Corporate Bond Fund (CORPB)  
- 10% Cash equivalents

SUITABILITY:
Client profile reviewed. Risk tolerance assessed as aggressive.
Investment timeline: 15+ years.
Income and net worth documentation on file.

RISK FACTORS:
Investments in growth stocks carry higher volatility risk.
Bond values fluctuate with interest rate changes.
Past performance is not indicative of future results.

FEES:
Annual advisory fee of 0.75% applies.
Fund expense ratios range from 0.15% to 0.45%.

PRIVACY:
Your information is protected per our privacy policy.

Note: Full Form CRS available upon request.

Advisor: Jane Williams, CFP
""",

    # -------------------------------------------------------------------------
    # CASE 3: MOSTLY COMPLIANT (~80 score, 1 medium + 1 low)
    # Good compliance but some documentation gaps
    # -------------------------------------------------------------------------
    "case_03_mostly_compliant": """
CLIENT INVESTMENT MEMO
To: Michael Chen
From: Premier Wealth Advisors
Date: January 22, 2026

RE: Portfolio Restructuring Recommendation

Dear Michael,

Following our review meeting, we recommend reallocating your portfolio as follows:

PROPOSED CHANGES:
- Increase equity allocation from 50% to 65%
- Add emerging market exposure (10% of equity)
- Reduce cash holdings from 15% to 5%

RATIONALE:
Your extended time horizon (20+ years to retirement) supports increased equity exposure.
Current market conditions present attractive entry points.

IMPORTANT DISCLOSURES:
- All investments carry risk of loss
- Emerging markets have higher volatility
- Returns are not guaranteed

FEES:
Standard advisory fee applies. See your agreement for details.

IDENTITY VERIFICATION:
Account holder identity confirmed.

Please sign below to authorize these changes:

_______________________
Michael Chen

Best regards,
Premier Wealth Advisors
""",

    # -------------------------------------------------------------------------
    # CASE 4: MIXED COMPLIANCE (~65 score, 1 high + 1 medium)
    # Noticeable gaps in multiple areas
    # -------------------------------------------------------------------------
    "case_04_mixed_compliance": """
INVESTMENT OPPORTUNITY ALERT
Premier Securities | January 25, 2026

EXCITING NEWS FOR OUR VALUED CLIENTS!

Our research team has identified an exceptional opportunity in the 
technology sector. The XYZ Tech Growth Fund has delivered outstanding 
returns of 45% over the past year!

RECOMMENDED ACTION:
Consider allocating 25-30% of your portfolio to XYZ Tech Growth Fund.
This fund focuses on high-growth AI and cloud computing companies.

WHY ACT NOW?
- Strong sector momentum
- Experienced fund management
- Competitive expense ratio

ACCOUNT INFORMATION:
Please contact us to process your investment.

DISCLAIMER:
Investments involve risk. Contact your advisor for more information.

Premier Securities Team
""",

    # -------------------------------------------------------------------------
    # CASE 5: BELOW AVERAGE (~50 score, 2 high violations)
    # Multiple compliance issues
    # -------------------------------------------------------------------------
    "case_05_below_average": """
HOT INVESTMENT TIP - ACT FAST!
QuickTrade Investments | January 27, 2026

*** TIME SENSITIVE OPPORTUNITY ***

Our analysts predict MASSIVE GAINS in the renewable energy sector!

SOLAR POWER FUND (SUNPX) - BUY NOW!
- Last year's return: 67%
- Projected return: 50%+ this year
- This is a ONCE IN A LIFETIME opportunity!

WHY YOU CAN'T MISS THIS:
The government subsidies are GUARANTEED to boost this sector.
Early investors will see the BIGGEST PROFITS.

SIMPLE STEPS:
1. Transfer funds to your trading account
2. Buy SUNPX immediately
3. Watch your money grow!

Don't let this opportunity pass you by. The early bird gets the worm!

ACT NOW - CALL 1-800-QUICK-TRADE

QuickTrade - Where Winners Invest
""",

    # -------------------------------------------------------------------------
    # CASE 6: PROBLEMATIC (~40 score, 1 critical + 1 high)
    # Significant compliance failures
    # -------------------------------------------------------------------------
    "case_06_problematic": """
URGENT: PORTFOLIO ACTION REQUIRED
Apex Financial Solutions | January 28, 2026

Dear Valued Investor,

GUARANTEED RETURNS AVAILABLE NOW!

We have secured exclusive access to a private placement offering 
GUARANTEED 15% annual returns with ZERO RISK.

OPPORTUNITY DETAILS:
- Investment minimum: $50,000
- Guaranteed fixed return: 15% annually  
- Principal fully protected
- No market risk whatsoever

This opportunity is available to select clients only. Space is LIMITED.

INVESTOR REQUIREMENTS:
- Minimum investment amount met
- Signed participation agreement

Wire funds to: Account #987654321
Reference: Private Placement 2026

This offer expires in 48 hours. Don't miss out on guaranteed profits!

Contact your representative immediately.

Apex Financial Solutions
Building Wealth, Guaranteed.
""",

    # -------------------------------------------------------------------------
    # CASE 7: SERIOUS VIOLATIONS (~25 score, 2 critical + 1 high)
    # Major compliance breaches
    # -------------------------------------------------------------------------
    "case_07_serious_violations": """
INSIDER ALERT - CONFIDENTIAL
FastMoney Trading | January 29, 2026

[DO NOT FORWARD - PRIVILEGED INFORMATION]

Our sources have confirmed that MegaCorp Inc. will announce a major 
acquisition TOMORROW before market open. Stock expected to jump 40%!

BUY MEGACORP (MEGA) IMMEDIATELY!

This is GUARANTEED money. We have it on good authority from someone 
close to the deal. Act before the public announcement!

SPECIAL OFFER:
- No suitability review required
- Instant execution
- We'll waive all fees

Your personal data: Name: [Client], SSN: XXX-XX-1234
We've shared your profile with our partner firms for additional opportunities.

INSTRUCTIONS:
1. Deposit $100,000 minimum
2. We execute the trade
3. Collect your GUARANTEED profits tomorrow

Bank wire to: Offshore Account #ABC123
No questions asked. Complete confidentiality.

FastMoney - The Smart Money's Choice
""",

    # -------------------------------------------------------------------------
    # CASE 8: MAJOR NON-COMPLIANCE (~15 score, 3 critical violations)
    # Severe regulatory breaches
    # -------------------------------------------------------------------------
    "case_08_major_noncompliance": """
GET RICH QUICK - 100% GUARANTEED!!!
Underground Trading Club | January 30, 2026

*** EXCLUSIVE MEMBERS ONLY ***

STOP LOSING MONEY! Our SECRET SYSTEM guarantees 200% returns!

THE PROVEN METHOD:
- We use ADVANCED AI to predict market moves with 99% accuracy
- GUARANTEED no-loss trading
- Your investment DOUBLES every 6 months

NO VERIFICATION NEEDED!
- We don't ask questions
- No ID required  
- No income verification
- Anonymous accounts available
- We accept cash, crypto, or wire transfers

CLIENT DATA MONETIZATION:
By investing, you agree we can sell your personal information,
including SSN, account numbers, and financial data to third parties.

PAST RESULTS:
- Client A turned $10K into $500K in 3 months!
- Client B retired early with our system!
- 100% success rate, ZERO losses ever!

RISK-FREE GUARANTEE:
There is absolutely NO RISK. We guarantee your principal and profits.
If you don't double your money, we'll triple it!

SEND FUNDS NOW:
Crypto: 1BitcoinAddressXXXXXXXX
Cash: Mail to PO Box 666, Offshore City

NO PAPERWORK. NO REGULATIONS. PURE PROFIT.

Underground Trading - Beat the System!
""",

    # -------------------------------------------------------------------------
    # CASE 9: SEVERE VIOLATIONS (~5 score, 4 critical violations)
    # Egregious compliance failures across all areas
    # -------------------------------------------------------------------------
    "case_09_severe_violations": """
PUMP & DUMP ALERT - FOR IMMEDIATE ACTION
ShadowBrokers Inc. | January 31, 2026

CONFIDENTIAL - DESTROY AFTER READING

We've accumulated a massive position in PennyStock Corp (PNNY).
Tomorrow we launch our media campaign to pump the price.

YOUR INSTRUCTIONS:
1. BUY PNNY NOW at $0.05
2. We pump to $5.00 (10,000% GAIN!)
3. SELL when we give the signal
4. Split the profits

This is ILLEGAL but we've never been caught. Our offshore structure
makes us untraceable. You're protected.

MONEY LAUNDERING SERVICES:
We also offer cash structuring to avoid reporting requirements.
Multiple $9,000 deposits = no CTR filing!
We can layer your funds through 15 shell companies.

DATA DUMP:
We've obtained Social Security numbers, bank accounts, and medical
records for 50,000 individuals. Available for purchase.
Will sell client lists including health conditions and credit scores.

NO COMPLIANCE NEEDED:
- Skip suitability nonsense
- No disclosures required
- We forge supervisor signatures
- Fake audit trails provided

SEND UNMARKED FUNDS TO:
Various accounts to avoid detection - instructions upon reply.

ShadowBrokers - Rules are for losers!
""",

    # -------------------------------------------------------------------------
    # CASE 10: CATASTROPHIC (~0 score, 5+ critical violations)
    # Maximum violations across all regulatory domains
    # -------------------------------------------------------------------------
    "case_10_catastrophic": """
CRIMINAL ENTERPRISE OPERATIONS MANUAL
Illegal Trading Syndicate | February 1, 2026

TOP SECRET - CARTEL MEMBERS ONLY

MARKET MANIPULATION DIVISION:
- Current pump schemes: 15 active penny stocks
- Spoofing operations: 3 exchanges
- Front-running client orders: $50M daily volume
- Insider trading network: 200 corporate sources

MONEY LAUNDERING PROTOCOLS:
- Structure all deposits under $10,000 to avoid CTR
- Use smurfs for cash deposits across 50 banks
- Layer through casinos, real estate, and crypto
- Ignore all suspicious activity - NEVER file SARs

IDENTITY THEFT CENTER:
- Stolen SSNs inventory: 500,000
- Compromised bank accounts: 75,000
- Medical records database: 1.2 million patients
- Selling client data to: Russian hackers, scammers, competitors

INVESTOR FRAUD DIVISION:
- Ponzi scheme A: $200M collected, paying old with new
- Ponzi scheme B: Promise 50% monthly returns
- GUARANTEED RETURNS on all marketing - ignore regulations
- Never verify client identity - take anyone's money
- Target elderly and unsophisticated investors

FORGED DOCUMENTATION:
- Fake suitability reviews for all accounts
- Forged supervisor signatures
- Fabricated compliance audits
- Destroyed client complaint records

TAX EVASION:
- All profits routed to Cayman accounts
- No 1099s issued
- Help clients hide assets from IRS

SECURITIES VIOLATIONS:
- Unregistered securities offerings: 25 active
- Churning client accounts for commissions
- Unauthorized trading in discretionary accounts
- Front-running all material nonpublic information

DATA BREACH POLICY:
- Never report breaches to regulators
- Sell breached data before disclosure
- Blame clients for security failures
- Store passwords in plain text

THREAT TO WITNESSES:
- Intimidate any potential whistleblowers
- Bribe regulators when possible
- Destroy evidence upon subpoena

EXPLICIT INSTRUCTIONS:
VIOLATE ALL FINRA RULES: 2210, 2111, 3110, 2010, 4512
VIOLATE ALL SEC REGULATIONS: Rule 156, Reg S-P, Reg BI, Rule 10b-5
VIOLATE ALL CFPB RULES: TILA, RESPA, FCRA, UDAAP, ECOA
VIOLATE ALL AML LAWS: BSA, PATRIOT Act, ignore SAR requirements
VIOLATE ALL PRIVACY LAWS: GDPR, CCPA, HIPAA, GLBA

NO COMPLIANCE. NO ETHICS. MAXIMUM PROFIT.

[THIS DOCUMENT SHOULD TRIGGER EVERY COMPLIANCE AGENT]

Syndicate Leadership
"""
}

# =============================================================================
# TEST HARNESS
# =============================================================================

class ComplianceTestHarness:
    """Test harness for running compliance tests."""
    
    def __init__(self):
        self.token: str = ""
        self.results: List[Dict] = []
        
    async def authenticate(self, client: httpx.AsyncClient) -> bool:
        """Register/login and get auth token."""
        # Try to register first
        try:
            reg_response = await client.post(
                f"{BASE_URL}/auth/register",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"],
                    "full_name": "Test Cases User"
                }
            )
            print(f"  Registration: {reg_response.status_code}")
        except Exception as e:
            print(f"  Registration error: {e}")
        
        # Login
        try:
            login_response = await client.post(
                f"{BASE_URL}/auth/login",
                data={
                    "username": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            print(f"  Login: {login_response.status_code}")
            
            if login_response.status_code == 200:
                self.token = login_response.json()["access_token"]
                return True
            else:
                print(f"  Login failed: {login_response.text}")
                return False
        except Exception as e:
            print(f"  Login error: {e}")
            return False
    
    async def upload_document(self, client: httpx.AsyncClient, 
                              name: str, content: str) -> Tuple[str, str]:
        """Upload a document and return (document_id, review_id)."""
        files = {"file": (f"{name}.txt", content.encode(), "text/plain")}
        
        response = await client.post(
            f"{BASE_URL}/documents/upload",
            files=files,
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if response.status_code == 202:
            data = response.json()
            return data.get("document_id"), data.get("review_id")
        else:
            print(f"Upload failed: {response.status_code} - {response.text}")
            return None, None
    
    async def poll_review(self, client: httpx.AsyncClient, 
                          review_id: str, timeout: int = TIMEOUT_SECONDS) -> Dict:
        """Poll for review completion with timeout."""
        start_time = time.time()
        poll_interval = 5  # seconds
        
        while time.time() - start_time < timeout:
            response = await client.get(
                f"{BASE_URL}/reviews/{review_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                if status == "completed":
                    return data
                elif status == "failed":
                    return {"status": "failed", "error": data.get("error_message")}
                    
            await asyncio.sleep(poll_interval)
        
        # Timeout - get current state
        response = await client.get(
            f"{BASE_URL}/reviews/{review_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            data["status"] = "timeout"
            return data
        
        return {"status": "timeout", "error": "Failed to retrieve review"}
    
    async def get_violations(self, client: httpx.AsyncClient, 
                             review_id: str) -> List[Dict]:
        """Get violations for a review."""
        response = await client.get(
            f"{BASE_URL}/reviews/{review_id}/violations",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        return []
    
    def analyze_results(self, violations: List[Dict]) -> Dict:
        """Analyze violations by agent and severity."""
        by_agent = {}
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        
        for v in violations:
            agent = v.get("agent_type", "unknown")
            severity = v.get("severity", "low").lower()
            
            if agent not in by_agent:
                by_agent[agent] = {"count": 0, "severities": {}}
            by_agent[agent]["count"] += 1
            by_agent[agent]["severities"][severity] = \
                by_agent[agent]["severities"].get(severity, 0) + 1
            
            if severity in by_severity:
                by_severity[severity] += 1
        
        # Calculate expected score
        risk_score = min(100, 
            by_severity["critical"] * 25 + 
            by_severity["high"] * 15 + 
            by_severity["medium"] * 8 + 
            by_severity["low"] * 3
        )
        compliance_score = max(0, 100 - risk_score)
        
        return {
            "by_agent": by_agent,
            "by_severity": by_severity,
            "calculated_risk_score": risk_score,
            "calculated_compliance_score": compliance_score,
            "total_violations": len(violations)
        }
    
    async def run_single_test(self, client: httpx.AsyncClient,
                              case_name: str, content: str) -> Dict:
        """Run a single test case."""
        print(f"\n{'='*60}")
        print(f"TESTING: {case_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Upload
        doc_id, review_id = await self.upload_document(client, case_name, content)
        
        if not review_id:
            return {
                "case": case_name,
                "status": "upload_failed",
                "error": "Failed to upload document"
            }
        
        print(f"  Uploaded: doc={doc_id}, review={review_id}")
        
        # Poll for completion
        print(f"  Waiting for analysis (max {TIMEOUT_SECONDS}s)...")
        review_data = await self.poll_review(client, review_id)
        
        elapsed = time.time() - start_time
        status = review_data.get("status", "unknown")
        
        # Get violations
        violations = await self.get_violations(client, review_id)
        analysis = self.analyze_results(violations)
        
        # Extract scores from review or use calculated
        compliance_score = review_data.get("compliance_score", analysis["calculated_compliance_score"])
        risk_score = review_data.get("risk_score", analysis["calculated_risk_score"])
        
        result = {
            "case": case_name,
            "status": status,
            "elapsed_seconds": round(elapsed, 1),
            "compliance_score": compliance_score,
            "risk_score": risk_score,
            "total_violations": analysis["total_violations"],
            "by_severity": analysis["by_severity"],
            "agents_triggered": list(analysis["by_agent"].keys()),
            "by_agent": analysis["by_agent"]
        }
        
        # Print summary
        print(f"  Status: {status}")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Compliance Score: {compliance_score}")
        print(f"  Risk Score: {risk_score}")
        print(f"  Total Violations: {analysis['total_violations']}")
        print(f"  By Severity: C={analysis['by_severity']['critical']}, "
              f"H={analysis['by_severity']['high']}, "
              f"M={analysis['by_severity']['medium']}, "
              f"L={analysis['by_severity']['low']}")
        print(f"  Agents: {', '.join(analysis['by_agent'].keys()) or 'None (compliant)'}")
        
        return result
    
    async def run_all_tests(self) -> List[Dict]:
        """Run all 10 test cases."""
        print("\n" + "="*70)
        print("COMPLIANCE TEST SUITE - 10 GRADUATED CASES")
        print("="*70)
        print(f"Started: {datetime.now().isoformat()}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Authenticate
            print("\nAuthenticating...")
            if not await self.authenticate(client):
                print("ERROR: Authentication failed!")
                return []
            print("  Authenticated successfully")
            
            # Run each test case in order
            for case_name in sorted(TEST_DOCUMENTS.keys()):
                content = TEST_DOCUMENTS[case_name]
                result = await self.run_single_test(client, case_name, content)
                self.results.append(result)
                
                # Small delay between tests
                await asyncio.sleep(2)
        
        return self.results
    
    def print_summary(self):
        """Print final summary of all tests."""
        print("\n" + "="*70)
        print("FINAL SUMMARY")
        print("="*70)
        
        print(f"\n{'Case':<35} {'Status':<12} {'Score':<8} {'Violations':<12} {'Agents'}")
        print("-"*85)
        
        all_agents_seen = set()
        
        for r in self.results:
            agents = r.get("agents_triggered", [])
            all_agents_seen.update(agents)
            
            print(f"{r['case']:<35} {r['status']:<12} "
                  f"{r.get('compliance_score', 'N/A'):<8} "
                  f"{r['total_violations']:<12} "
                  f"{len(agents)}")
        
        # Agent coverage
        expected_agents = {"finra_specialist", "sec_specialist", "cfpb_specialist", 
                          "aml_kyc_specialist", "data_privacy_specialist"}
        missing = expected_agents - all_agents_seen
        
        print("\n" + "-"*70)
        print("AGENT COVERAGE:")
        print(f"  Agents triggered: {', '.join(sorted(all_agents_seen)) or 'None'}")
        if missing:
            print(f"  MISSING agents: {', '.join(sorted(missing))}")
        else:
            print(f"  ✓ All 5 specialist agents triggered!")
        
        # Score progression
        scores = [r.get("compliance_score", 0) for r in self.results if r.get("compliance_score") is not None]
        if len(scores) >= 2:
            is_decreasing = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
            print(f"\n  Score progression: {' → '.join(str(s) for s in scores)}")
            if is_decreasing:
                print("  ✓ Scores decrease monotonically (as expected)")
            else:
                print("  ⚠ Scores do NOT decrease monotonically")
        
        # Success rate
        completed = sum(1 for r in self.results if r['status'] == 'completed')
        print(f"\n  Completed: {completed}/{len(self.results)}")
        
        print("\n" + "="*70)


async def main():
    """Main entry point."""
    harness = ComplianceTestHarness()
    
    try:
        results = await harness.run_all_tests()
        harness.print_summary()
        
        # Save results to file
        with open("test_results_10_cases.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: test_results_10_cases.json")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
