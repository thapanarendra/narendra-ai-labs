#!/bin/bash

# Naukri Profile Tracker - Quick Start Script
# This script sets up and runs the Naukri Profile Tracker agent

set -e

echo "🎯 Naukri Profile Tracker - Setup Script"
echo "========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10+ is required. Current version: $python_version"
    exit 1
fi
echo "✓ Python version: $python_version"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "🔐 Please edit .env file with your Naukri credentials:"
    echo "   - NAUKRI_EMAIL"
    echo "   - NAUKRI_PASSWORD"
    echo "   - RESUME_PATH"
    echo ""
    echo "Then run this script again or use: python main.py"
    exit 0
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Available commands:"
echo "  python main.py run --task full-check    # Run full profile check"
echo "  python main.py run --task resume-update # Update resume"
echo "  python main.py run --task recruiter-check # Check recruiter activity"
echo "  python main.py daemon                   # Run as scheduled daemon"
echo "  python main.py status                   # Show configuration status"
echo "  python main.py history                  # Show activity history"
echo ""
echo "📖 See README.md for more details"
