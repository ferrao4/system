#!/bin/bash

echo "🤖 Starting AI Calling Bot..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please create a .env file with your API keys."
    echo "Check README.md for setup instructions."
    echo ""
    echo "Creating template .env file..."
    cp .env .env.example 2>/dev/null || true
fi

# Start the application
echo "🚀 Starting AI Calling Bot server..."
echo "Access the web interface at: http://localhost:8000"
echo "API documentation at: http://localhost:8000/docs"
echo ""
python ai_calling_bot.py