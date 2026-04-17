#!/bin/bash

set -e

echo "✨ FitFinder MVP - Quick Start"
echo "================================"

# Backend setup
echo ""
echo "📦 Setting up Backend..."
cd backend

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    cp .env.example .env
fi

echo "✅ Backend ready!"

# Frontend setup
echo ""
echo "📦 Setting up Frontend..."
cd ../frontend

npm install -q

echo "✅ Frontend ready!"

echo ""
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""
echo "Start in two terminals:"
echo ""
echo "Terminal 1 - Backend:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "Terminal 2 - Frontend:"
echo "  cd frontend" 
echo "  npm run dev"
echo ""
echo "Then visit: http://localhost:5173"
echo ""
