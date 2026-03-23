#!/bin/bash

# NXW Backend Server Startup Script
# Kills any existing processes and starts fresh

echo "🔧 Stopping any existing servers..."
pkill -f uvicorn 2>/dev/null
pkill -f "python.*app.py" 2>/dev/null

echo "⏳ Waiting for ports to free..."
sleep 2

echo "🚀 Starting NXW backend server..."
cd /home/jgcampbell300/PycharmProjects/nxw
source .venv/bin/activate
export PYTHONPATH=/home/jgcampbell300/PycharmProjects/nxw:$PYTHONPATH

# Try port 8000 first, fallback to 8001
if lsof -i :8000 >/dev/null 2>&1; then
    echo "📡 Port 8000 in use, trying 8001..."
    uvicorn backend.app:app --reload --host 0.0.0.0 --port 8001
else
    echo "📡 Starting on port 8000..."
    uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
fi
