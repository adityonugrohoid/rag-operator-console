#!/bin/bash
# Setup Python virtual environment and install dependencies
set -e

echo "Setting up Python virtual environment for rag-operator-console..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "✓ Virtual environment setup complete!"
echo "To activate: source .venv/bin/activate"
echo "To run tests: pytest"
