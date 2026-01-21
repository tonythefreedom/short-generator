#!/bin/bash
# Start FastAPI backend server

set -e

cd "$(dirname "$0")/../backend"

echo "Starting FastAPI backend server..."
echo "Backend will be available at http://localhost:8000"
echo ""

source ../venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
