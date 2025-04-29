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

# Start Streamlit
echo "Starting Streamlit dashboard..."
python -m streamlit run src/dashboard/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.maxUploadSize=50 \
    --server.maxMessageSize=50 \
    --browser.serverPort=8501 \
    --browser.gatherUsageStats=false
