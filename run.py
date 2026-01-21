#!/usr/bin/env python3
"""
Run script for WAN 2.2 Short Video Generator
This script starts the FastAPI server which serves both the API and the React frontend.
"""
import uvicorn
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend/app"]
    )
