"""Check review status."""
import asyncio
import httpx

async def check():
    async with httpx.AsyncClient() as client:
        resp = await client.get('http://localhost:8001/api/v1/reviews/c21ed5f6-e6f5-4afb-9750-e7854480a1a5')
        print(f"Status Code: {resp.status_code}")
        data = resp.json()
        print(f"Review Status: {data.get('status')}")
        print(f"Compliance Score: {data.get('compliance_score')}")
        print(f"Risk Score: {data.get('risk_score')}")
        violations = data.get('violations', [])
        print(f"Violations Found: {len(violations)}")
        
        for i, v in enumerate(violations[:5], 1):
            print(f"\n[{i}] {v.get('regulation', 'N/A')}")
            print(f"    Severity: {v.get('severity')}")
            print(f"    Agent: {v.get('agent_source')}")
            print(f"    Text: {v.get('original_text', '')[:100]}...")

asyncio.run(check())
