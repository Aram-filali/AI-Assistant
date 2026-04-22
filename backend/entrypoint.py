#!/usr/bin/env python3
"""
Entrypoint for Railway deployment.
Initializes database, then starts Uvicorn.
"""
import subprocess
import sys
import os

def init_database():
    """Initialize database by creating tables."""
    print("=" * 60, flush=True)
    print("🚀 Starting Database Initialization", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)
    
    try:
        # Import and run the init_db function
        from app.core.init_db import init_database as create_tables
        create_tables()
        
    except Exception as e:
        print(flush=True)
        print("=" * 60, flush=True)
        print(f"❌ Database Initialization FAILED: {e}", flush=True)
        print("=" * 60, flush=True)
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
    init_database()
    start_uvicorn()

