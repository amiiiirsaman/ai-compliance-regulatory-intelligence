"""Helper script to start the server from any directory."""
import os
import sys
import subprocess

# Change to the backend directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

# Add to Python path
sys.path.insert(0, backend_dir)

# Start uvicorn
subprocess.run([
    sys.executable, "-m", "uvicorn", 
    "app.main:app", 
    "--host", "127.0.0.1", 
    "--port", "8001"
])
