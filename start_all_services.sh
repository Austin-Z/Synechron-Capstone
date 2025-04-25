#!/bin/bash

# Run database migrations
/app/check_db_env.sh
echo "Starting database migrations..."
python -m alembic upgrade head

# Import database if needed
if [ -f "migrations/database_backup.sql" ]; then
    # Only try to import if DATABASE_URL is not set (local development)
    if [ -z "$DATABASE_URL" ]; then
        mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < migrations/database_backup.sql || echo "Database import failed but continuing..."
    else
        echo "Skipping database import in Railway environment"
    fi
fi

# Start Express server in the background on port 8080
echo "Starting Express server on port 8080..."
EXPRESS_PORT=8080
export EXPRESS_PORT
node /app/express_server.js &
EXPRESS_PID=$!
echo "Express server started with PID: $EXPRESS_PID on port $EXPRESS_PORT"

# Start Nginx in the background
echo "Starting Nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!
echo "Nginx started with PID: $NGINX_PID"

# Start Streamlit on port 3001 (avoid using 3000 which is reserved)
echo "Starting Streamlit on port 3001..."
STREAMLIT_PORT=3001
python -m streamlit run src/dashboard/app.py \
    --server.port=$STREAMLIT_PORT \
    --server.address=0.0.0.0 \
    --server.maxUploadSize=50 \
    --server.maxMessageSize=50 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --browser.serverPort=$STREAMLIT_PORT \
    --browser.gatherUsageStats=false

# If Streamlit exits, kill the other processes
kill $EXPRESS_PID
kill $NGINX_PID
