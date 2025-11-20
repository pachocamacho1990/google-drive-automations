#!/bin/bash

# Google Drive Automation - Virtual Environment Setup

echo "Setting up Python virtual environment for Google Drive automation..."

# Detect Python version (prefer 3.12, but accept 3.11+)
PYTHON_CMD=""
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo "Error: Python 3.11+ is required but not installed."
    exit 1
fi

# Display detected Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "Using $PYTHON_VERSION"

# Check if venv exists
if [ -d "venv" ]; then
    echo "Virtual environment already exists."
    read -p "Delete and recreate? This will remove all installed packages. (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
    else
        echo "Setup cancelled. Keeping existing environment."
        exit 0
    fi
fi

# Create virtual environment with explicit Python version
echo "Creating virtual environment with $PYTHON_CMD..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "To activate the environment:"
echo "  source venv/bin/activate"
echo ""
echo "To run automations:"
echo "  source venv/bin/activate && python automations/labels_lister.py"
echo ""
echo "To test utilities import:"
echo "  source venv/bin/activate && python -c \"from utilities import *; print('✅ Utilities loaded')\""
echo ""
echo "To deactivate:"
echo "  deactivate"