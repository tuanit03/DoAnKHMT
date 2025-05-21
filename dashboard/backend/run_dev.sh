#!/bin/bash
# Development startup script

# Set development environment variables
export PYTHONPATH=$(pwd)

# Initialize database (if needed)
echo "Initializing database..."
python init_db.py

# Start the FastAPI application with auto-reload
echo "Starting FastAPI application..."
uvicorn app:app --host 0.0.0.0 --port 8000 --reload