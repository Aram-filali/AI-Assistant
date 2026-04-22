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
    print("=" * 60, flush=True)
    print("🚀 Starting Database Migrations", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)
    
    try:
        # Run alembic with subprocess, capturing output
        process = subprocess.Popen(
            ["alembic", "upgrade", "head"],
            cwd="/app",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        # Print output line by line as it comes
        for line in process.stdout:
            print(line, end='', flush=True)
        
        returncode = process.wait()
        
        if returncode == 0:
            print(flush=True)
            print("=" * 60, flush=True)
            print("✅ Migrations COMPLETED successfully!", flush=True)
            print("=" * 60, flush=True)
            print(flush=True)
        else:
            print(flush=True)
            print("=" * 60, flush=True)
            print("❌ Migrations FAILED!", flush=True)
            print("=" * 60, flush=True)
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error running migrations: {e}", flush=True)
        sys.exit(1)

def start_uvicorn():
    """Start Uvicorn application server."""
    print("🚀 Starting FastAPI application...", flush=True)
    print(flush=True)
    
    os.execvp("uvicorn", [
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])

if __name__ == "__main__":
    run_migrations()
    start_uvicorn()

