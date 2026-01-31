#!/bin/sh
# Entrypoint script for Railway deployment
# This ensures PORT environment variable is properly used

set -e

# Use PORT from environment or default to 8000
PORT=${PORT:-8000}

# Run uvicorn with the port
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"

