#!/bin/bash
# Setup script for Digital Twin AI

set -e

echo "🚀 Setting up Digital Twin AI..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Download NLTK data
echo "Downloading NLTK data..."
python3 -c "import nltk; nltk.download('punkt', quiet=True)"

# Create directories
echo "Creating directories..."
mkdir -p data/raw data/processed data/chroma models outputs

# Copy .env.example if .env doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env from .env.example - please configure it"
    else
        echo "⚠️ .env.example not found - create .env manually"
    fi
else
    echo "✅ .env already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure .env file"
echo "2. Export your data to data/raw/"
echo "3. Run: python src/data_prep.py"
echo "4. Run: python src/train.py"
echo "5. Run: python src/rag.py --dataset data/processed/train.jsonl"
echo "6. Start API: uvicorn src.server:app"