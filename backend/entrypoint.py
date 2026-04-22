#!/usr/bin/env python3
"""
Entrypoint for Railway deployment.
Runs migrations, then starts Uvicorn.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_migrations():
    """Run Alembic migrations."""
    print("=" * 50)
    print("🚀 Starting Database Migrations")
    print("=" * 50)
    print()
    
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd="/app",
            check=False
        )
        
        if result.returncode == 0:
            print()
            print("=" * 50)
            print("✅ Migrations COMPLETED successfully!")
            print("=" * 50)
            print()
        else:
            print()
            print("=" * 50)
            print("❌ Migrations FAILED!")
            print("=" * 50)
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        sys.exit(1)

def start_uvicorn():
    """Start Uvicorn application server."""
    print("🚀 Starting FastAPI application...")
    print()
    
    os.execvp("uvicorn", [
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])

if __name__ == "__main__":
    run_migrations()
    start_uvicorn()
