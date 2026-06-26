"""
Run the complete 10-case compliance test suite.
This script starts the server in a subprocess and runs the tests.
"""

import asyncio
import subprocess
import sys
import time
import os

# Change to backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

async def run_tests():
    """Run the test suite."""
    
    # Import the test module
    from test_10_cases import ComplianceTestHarness
    import json
    
    harness = ComplianceTestHarness()
    
    try:
        results = await harness.run_all_tests()
        harness.print_summary()
        
        # Save results
        with open("test_results_10_cases.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: test_results_10_cases.json")
        
        return results
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    # Start server in subprocess
    print("Starting server...")
    server_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    print("Waiting for server to be ready...")
    time.sleep(8)
    
    # Check if server is running
    if server_proc.poll() is not None:
        print("Server failed to start!")
        stdout, stderr = server_proc.communicate()
        print(f"STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
        return
    
    print("Server is running")
    
    try:
        # Run tests
        results = asyncio.run(run_tests())
    finally:
        # Stop server
        print("\nStopping server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        print("Server stopped")

if __name__ == "__main__":
    main()
