"""Test registration endpoint."""
import asyncio
import httpx
import time

async def test_register():
    unique_email = f"user_{int(time.time())}@example.com"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "Test123456",
                "full_name": "New Test User"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_register())
