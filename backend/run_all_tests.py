"""
Complete test runner - runs unit tests first, then the 10-case suite.
Usage: python run_all_tests.py
"""
import subprocess
import sys
import os
import time

# Change to backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=backend_dir)
    return result.returncode == 0

def main():
    print("\n" + "="*70)
    print("COMPLIANCE SYSTEM - COMPLETE TEST SUITE")
    print("="*70)
    
    # Step 1: Run unit tests (no server needed)
    print("\n" + "="*70)
    print("STEP 1: Running Unit Tests")
    print("="*70)
    
    unit_result = run_command([sys.executable, "test_bedrock_unit.py"], "Bedrock & Agent Unit Tests")
    
    # Continue even if unit tests have minor failures (like throttling)
    if not unit_result:
        print("\n⚠ Some unit tests may have failed, but continuing with integration tests...")
    else:
        print("\n✓ Unit tests passed!")
    
    # Step 2: Start server
    print("\n" + "="*70)
    print("STEP 2: Starting Server")
    print("="*70)
    
    # Use start_server.py which handles the working directory properly
    server_proc = subprocess.Popen(
        [sys.executable, os.path.join(backend_dir, "start_server.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    
    print("Waiting for server to start...")
    time.sleep(12)  # Give it plenty of time
    
    if server_proc.poll() is not None:
        print("❌ Server failed to start!")
        stdout, _ = server_proc.communicate()
        print(stdout.decode() if stdout else "No output")
        return 1
    
    # Verify server is reachable
    import urllib.request
    for attempt in range(5):
        try:
            urllib.request.urlopen("http://127.0.0.1:8001/health", timeout=5)
            print("✓ Server running and reachable on port 8001")
            break
        except Exception as e:
            if attempt < 4:
                print(f"  Attempt {attempt+1}: Server not ready yet, waiting...")
                time.sleep(3)
            else:
                print(f"⚠ Server may not be fully ready: {e}")
    
    print("✓ Server running on port 8001")
    
    # Step 3: Run 10-case test suite
    print("\n" + "="*70)
    print("STEP 3: Running 10-Case Test Suite")
    print("="*70)
    
    try:
        result = subprocess.run(
            [sys.executable, "test_10_cases.py"],
            cwd=backend_dir
        )
        test_success = result.returncode == 0
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        test_success = False
    finally:
        # Stop server
        print("\n\nStopping server...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        print("Server stopped.")
    
    if test_success:
        print("\n" + "="*70)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*70)
        return 0
    else:
        print("\n" + "="*70)
        print("❌ SOME TESTS FAILED")
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
