# Streamlit dashboard application


FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    default-mysql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt && python -m streamlit --version

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH="/usr/local/bin:$PATH"
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_RUN_ON_SAVE=false
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV PORT=8501

# Set a script to check for DATABASE_URL and set appropriate environment variables
RUN echo '#!/bin/bash\n\
# Check for Railway-specific environment variables\n\
if [ ! -z "$RAILWAY_MYSQL_URL" ]; then\n\
  echo "RAILWAY_MYSQL_URL found, setting DATABASE_URL"\n\
  export DATABASE_URL="$RAILWAY_MYSQL_URL"\n\
fi\n\
\n\
# Check for DATABASE_URL\n\
if [ ! -z "$DATABASE_URL" ]; then\n\
  echo "DATABASE_URL found: $DATABASE_URL"\n\
  # Clear any hardcoded database settings to ensure DATABASE_URL takes precedence\n\
  unset DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME\n\
else\n\
  # Check for Railway-provided MySQL variables\n\
  if [ ! -z "$MYSQLHOST" ] && [ ! -z "$MYSQLPASSWORD" ]; then\n\
    echo "Railway MySQL variables found, constructing DATABASE_URL"\n\
    export DATABASE_URL="mysql://$MYSQLUSER:$MYSQLPASSWORD@$MYSQLHOST:$MYSQLPORT/$MYSQL_DATABASE"\n\
    echo "Set DATABASE_URL to: $DATABASE_URL"\n\
    # Clear any hardcoded database settings\n\
    unset DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME\n\
  else\n\
    echo "No Railway database variables found, using default database settings"\n\
  fi\n\
fi' > /app/check_db_env.sh && chmod +x /app/check_db_env.sh

# Create a startup script to run Streamlit
RUN echo '#!/bin/bash\n\
# Run database migrations\n\
/app/check_db_env.sh\n\
echo "Starting database migrations..."\n\
python -m alembic upgrade head\n\
\n\
# Import database if needed\n\
if [ -f "migrations/database_backup.sql" ]; then\n\
    # Only try to import if DATABASE_URL is not set (local development)\n\
    if [ -z "$DATABASE_URL" ]; then\n\
        mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME < migrations/database_backup.sql || echo "Database import failed but continuing..."\n\
    else\n\
        echo "Skipping database import in Railway environment"\n\
    fi\n\
fi\n\
\n\
# Start Streamlit\n\
echo "Starting Streamlit..."\n\
python -m streamlit run src/dashboard/app.py \\\
    --server.port=$PORT \\\
    --server.address=0.0.0.0 \\\
    --server.maxUploadSize=50 \\\
    --server.maxMessageSize=50 \\\
    --browser.serverPort=$PORT \\\
    --browser.gatherUsageStats=false\n\
' > /app/start.sh && chmod +x /app/start.sh

# Add after copying the application code
COPY alembic.ini .
COPY alembic ./alembic
COPY migrations ./migrations

# Command to run the Streamlit dashboard
CMD ["/app/start.sh"]
