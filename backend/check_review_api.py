"""Check a specific review via API."""
import requests

# The review that showed COMPLETE in database
REVIEW_ID = "c21ed5f6-e6f5-4afb-9750-e7854480a1a5"
BASE_URL = "http://localhost:8001"

# First login to get token
resp = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    data={
        "username": "compliance_test_1770170537@example.com",
        "password": "TestPassword123!"
    }
)

if resp.status_code != 200:
    # Try creating new user
    print("Creating new user...")
    resp = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json={
            "email": "admin_check@example.com",
            "password": "TestPassword123!",
            "full_name": "Admin Check"
        }
    )
    print(f"Register: {resp.status_code}")
    
    resp = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={
            "username": "admin_check@example.com",
            "password": "TestPassword123!"
        }
    )

if resp.status_code == 200:
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get the review
    resp = requests.get(
        f"{BASE_URL}/api/v1/reviews/{REVIEW_ID}",
        headers=headers
    )
    
    if resp.status_code == 200:
        data = resp.json()
        print("=" * 60)
        print("REVIEW RESULTS FROM API")
        print("=" * 60)
        print(f"Status: {data.get('status')}")
        print(f"Compliance Score: {data.get('compliance_score')}")
        print(f"Risk Score: {data.get('risk_score')}")
        print(f"Summary: {data.get('summary', 'N/A')[:200]}...")
        
        violations = data.get("violations", [])
        print(f"\nViolations Found: {len(violations)}")
        
        for i, v in enumerate(violations[:10], 1):
            print(f"\n[{i}] {v.get('regulation')}")
            print(f"    Severity: {v.get('severity')}")
            print(f"    Agent: {v.get('agent_source')}")
            print(f"    Explanation: {v.get('explanation', '')[:150]}...")
    else:
        print(f"Error getting review: {resp.status_code}")
        print(resp.text)
else:
    print(f"Login failed: {resp.status_code}")
    print(resp.text)
