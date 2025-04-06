#!/bin/bash

# Kill any existing processes on port 5000
pkill -f "gunicorn|uvicorn" || true

# Start the application using the run.sh script
./run.sh
