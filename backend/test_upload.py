"""Test document upload endpoint."""
import asyncio
import httpx

async def test_upload():
    # First login to get token
    async with httpx.AsyncClient() as client:
        login_response = await client.post(
            "http://localhost:8001/api/v1/auth/login",
            data={
                "username": "user_1770166731@example.com",
                "password": "Test123456"
            }
        )
        print(f"Login Status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print("Login failed, creating new user...")
            import time
            email = f"testuser_{int(time.time())}@example.com"
            reg_response = await client.post(
                "http://localhost:8001/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "Test123456",
                    "full_name": "Test User"
                }
            )
            print(f"Register: {reg_response.status_code}")
            
            login_response = await client.post(
                "http://localhost:8001/api/v1/auth/login",
                data={"username": email, "password": "Test123456"}
            )
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        print(f"Got access token")
        
        # Upload document
        with open("d:/ai_Agentic_Compliance/test_compliance_document.txt", "rb") as f:
            files = {"file": ("test_compliance_document.txt", f, "text/plain")}
            upload_response = await client.post(
                "http://localhost:8001/api/v1/documents/upload",
                headers={"Authorization": f"Bearer {access_token}"},
                files=files
            )
        
        print(f"Upload Status: {upload_response.status_code}")
        print(f"Upload Response: {upload_response.text}")

if __name__ == "__main__":
    asyncio.run(test_upload())
