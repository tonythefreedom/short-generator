#!/bin/bash
# Start ComfyUI server

set -e

cd "$(dirname "$0")/../comfyui"

echo "Starting ComfyUI server..."
echo "ComfyUI will be available at http://localhost:8188"
echo ""

source venv/bin/activate
python main.py --listen --port 8188
