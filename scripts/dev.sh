#!/bin/bash
# Development script - runs both frontend dev server and backend

set -e

# Start backend in background
echo "Starting backend server..."
cd "$(dirname "$0")/.."
source venv/bin/activate 2>/dev/null || true

# Run backend
python run.py &
BACKEND_PID=$!

# Start frontend dev server
echo "Starting frontend dev server..."
cd frontend
npm run dev &
FRONTEND_PID=$!

# Trap ctrl+c and kill both processes
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

echo ""
echo "Backend running at http://localhost:8000"
echo "Frontend dev server running at http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"

wait
