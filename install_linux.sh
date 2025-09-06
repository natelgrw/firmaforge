#!/bin/bash
# FirmaForge Linux Installation Script

echo "🔧 Installing FirmaForge on Linux..."

# Check for conda
if ! command -v conda &> /dev/null; then
    echo "❌ Conda not found. Install Miniconda/Anaconda first:"
    echo "   https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi
echo "✅ Conda found"

# Create conda environment
echo "📦 Creating conda environment from ffenv.yml..."
conda env create -f ffenv.yml || echo "⚠️ Environment may already exist, continuing..."

# Install FirmaForge in dev mode
echo "🚀 Installing FirmaForge in development mode..."
conda run -n ffenv pip install -e .

# Install Linux system dependencies
if command -v apt-get &> /dev/null; then
    echo "📦 Installing system dependencies via apt..."
    sudo apt update
    sudo apt install -y squashfs-tools p7zip-full e2fsprogs cramfsprogs ubi-utils jefferson || echo "⚠️ Some packages may not be available"
elif command -v yum &> /dev/null; then
    echo "📦 Installing system dependencies via yum..."
    sudo yum install -y squashfs-tools p7zip e2fsprogs cramfsprogs ubi-utils || echo "⚠️ Some packages may not be available"
else
    echo "⚠️ Package manager not found. Install dependencies manually."
fi

echo "🎉 Installation complete! Activate: conda activate ffenv"