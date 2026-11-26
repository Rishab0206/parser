#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "=========================================="
echo " Building Banking Parser Engine on Render"
echo "=========================================="

# 1. Install Backend Dependencies
echo "--> Installing Python dependencies..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# 2. Build Frontend if Node/NPM is available in the environment
if command -v npm &> /dev/null; then
  echo "--> Node/NPM detected! Building React Frontend..."
  cd frontend
  npm install
  npm run build
  cd ..
  echo "--> Frontend build complete and ready for FastAPI static serving."
else
  echo "--> Native Python runtime detected without Node."
fi

echo "=========================================="
echo " Active Render Profile Build Successful!"
echo "=========================================="
