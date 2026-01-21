#!/bin/bash
# Setup script for WAN 2.2 Short Video Generator

set -e

echo "=== WAN 2.2 Short Video Generator Setup ==="
echo ""

# Check if pyenv is available
if command -v pyenv &> /dev/null; then
    echo "Using pyenv to set Python 3.12.11..."
    pyenv install -s 3.12.11
    pyenv local 3.12.11
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3.12 -m venv venv || python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r backend/requirements.txt

# Install frontend dependencies and build
echo "Installing frontend dependencies..."
cd frontend
npm install

echo "Building frontend..."
npm run build
cd ..

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""
echo "Then open http://localhost:8000 in your browser"
