#!/usr/bin/env python
"""Setup script for Compliance & Regulatory Intelligence System backend."""
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with error code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        return False


def main():
    """Main setup function."""
    print("\n" + "="*60)
    print("🚀 Compliance Intelligence System - Backend Setup")
    print("="*60)
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Check Python version
    print(f"\n📌 Python version: {sys.version}")
    if sys.version_info < (3, 11):
        print("⚠️  Warning: Python 3.11+ is recommended")
    
    # Step 1: Create virtual environment if it doesn't exist
    venv_path = script_dir / "venv"
    if not venv_path.exists():
        if not run_command(
            [sys.executable, "-m", "venv", "venv"],
            "Creating virtual environment"
        ):
            print("\n❌ Failed to create virtual environment")
            return 1
    else:
        print(f"\n✅ Virtual environment already exists at {venv_path}")
    
    # Step 2: Determine pip path
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    # Step 3: Upgrade pip
    run_command(
        [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
        "Upgrading pip"
    )
    
    # Step 4: Install dependencies
    requirements_file = script_dir / "requirements.txt"
    if requirements_file.exists():
        if not run_command(
            [str(pip_path), "install", "-r", "requirements.txt"],
            "Installing dependencies from requirements.txt"
        ):
            print("\n❌ Failed to install dependencies")
            return 1
    else:
        print(f"\n❌ requirements.txt not found at {requirements_file}")
        return 1
    
    # Step 5: Check .env file
    env_file = script_dir / ".env"
    env_example = script_dir / ".env.example"
    
    if not env_file.exists():
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("\n⚠️  Created .env from .env.example - please update with your credentials")
        else:
            print("\n⚠️  No .env file found - please create one with required variables")
    else:
        print(f"\n✅ .env file exists at {env_file}")
    
    # Print success message
    print("\n" + "="*60)
    print("🎉 Setup completed successfully!")
    print("="*60)
    print("\n📋 Next steps:")
    print("   1. Update .env with your AWS credentials and database URL")
    print("   2. Ensure PostgreSQL is running")
    print("   3. Activate virtual environment:")
    if sys.platform == "win32":
        print("      .\\venv\\Scripts\\activate")
    else:
        print("      source venv/bin/activate")
    print("   4. Start the server:")
    print("      uvicorn app.main:app --reload --port 8001")
    print("")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
