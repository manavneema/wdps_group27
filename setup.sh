#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Updating package lists and installing dependencies..."
sudo apt-get update && sudo apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    cmake \
    pkg-config \
    && sudo rm -rf /var/lib/apt/lists/*

echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel --no-cache-dir 
pip install --prefer-binary spacy --no-cache-dir
pip install -r requirements.txt --no-cache-dir
python -m spacy download en_core_web_md


echo "Setup completed successfully!"

