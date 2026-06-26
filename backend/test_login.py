"""Test login endpoint."""
import asyncio
import httpx

async def test_login():
    async with httpx.AsyncClient() as client:
        # Login with the user we just created
        response = await client.post(
            "http://localhost:8001/api/v1/auth/login",
            data={
                "username": "user_1770166731@example.com",
                "password": "Test123456"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_login())
