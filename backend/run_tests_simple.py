"""
Simple test runner that runs the 10-case test suite.
Assumes server is already running on port 8001.
"""
import subprocess
import sys
import time
import urllib.request

def check_server():
    """Check if server is running."""
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8001/health", timeout=5)
        return req.status == 200
    except:
        return False

def main():
    print("=" * 70)
    print("COMPLIANCE TEST SUITE - SIMPLE RUNNER")
    print("=" * 70)
    
    # Check if server is running
    print("\nChecking server status...")
    if check_server():
        print("✓ Server is running on port 8001")
    else:
        print("✗ Server is NOT running!")
        print("\nPlease start the server manually in another terminal:")
        print("  cd d:\\ai_Agentic_Compliance\\backend")
        print("  python -m uvicorn app.main:app --host 127.0.0.1 --port 8001")
        print("\nThen run this script again.")
        return 1
    
    # Run the tests
    print("\n" + "=" * 70)
    print("Running 10-Case Test Suite...")
    print("=" * 70 + "\n")
    
    result = subprocess.run(
        [sys.executable, "test_10_cases.py"],
        cwd="d:\\ai_Agentic_Compliance\\backend"
    )
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
