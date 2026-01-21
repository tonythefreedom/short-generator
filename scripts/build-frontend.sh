#!/bin/bash
# Build frontend script

set -e

cd "$(dirname "$0")/../frontend"

echo "Installing dependencies..."
npm install

echo "Building frontend..."
npm run build

echo "Frontend built successfully!"
echo "Static files are in frontend/dist/"
