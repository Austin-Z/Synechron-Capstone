#!/bin/bash

# Start Express server in the background
echo "Starting Express server on port 8080..."
EXPRESS_PORT=8080
export EXPRESS_PORT
cd /app && node express_server.js &
EXPRESS_PID=$!
echo "Express server started with PID: $EXPRESS_PID on port $EXPRESS_PORT"

# Start Streamlit on port 3001
echo "Starting Streamlit on port 3001..."
STREAMLIT_PORT=3001
export STREAMLIT_PORT
cd /app && python -m streamlit run src/dashboard/app.py \
    --server.port=$STREAMLIT_PORT \
    --server.address=0.0.0.0 \
    --server.baseUrlPath=dashboard \
    --server.maxUploadSize=50 \
    --server.maxMessageSize=50 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.serverPort=$STREAMLIT_PORT \
    --browser.gatherUsageStats=false

# If Streamlit exits, kill the Express server
kill $EXPRESS_PID
