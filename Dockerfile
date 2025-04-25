# Multi-stage build for both React frontend and Streamlit backend

# React frontend build stage
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copy frontend package files
COPY frontend/package.json frontend/package-lock.json* ./frontend/

# Install dependencies
WORKDIR /app/frontend
RUN npm install

# Install Express for the fallback server
RUN npm install express --save

# Copy frontend source code
COPY frontend/ ./

# Build the React app with CI=false to prevent failing on warnings
RUN CI=false npm run build

# Verify the build output with more details
RUN echo "Frontend build contents:" && ls -la build && \
    echo "Index.html content:" && cat build/index.html | head -20

# Python backend build stage
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Final runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies including Nginx and Node.js
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    default-mysql-client \
    curl \
    nginx \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && node --version \
    && npm --version \
    && npm install -g express \
    && rm -rf /var/lib/apt/lists/*

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy application code
COPY . .

# Make sure test_nginx.html is in the right place and readable
RUN ls -la /app/test_nginx.html || echo "test_nginx.html is missing!" && \
    chmod 644 /app/test_nginx.html || echo "Could not chmod test_nginx.html" && \
    cp /app/test_nginx.html /app/test_nginx.html.backup || echo "Could not create backup"

# Copy Express server file, package.json, and startup script
COPY express_server.js /app/express_server.js
COPY package.json /app/package.json
COPY start_all_services.sh /app/start_all_services.sh
RUN chmod +x /app/start_all_services.sh

# Install Express dependencies
WORKDIR /app
RUN npm install && \
    npm install http-proxy-middleware@^3.0.4 && \
    npm list

# Copy React frontend build from frontend-builder
COPY --from=frontend-builder /app/frontend/build /app/frontend/build

# Verify frontend build files exist with more details
RUN ls -la /app/frontend/build || echo "Frontend build directory is empty or missing!" && \
    if [ -f "/app/frontend/build/index.html" ]; then \
        echo "index.html exists in build directory"; \
        cat /app/frontend/build/index.html | head -20; \
    else \
        echo "index.html is missing from build directory"; \
        # Create a simple index.html as fallback
        mkdir -p /app/frontend/build; \
        echo '<!DOCTYPE html><html><head><title>FOFs Dashboard</title></head><body><h1>FOFs Dashboard</h1><p>Frontend build may be missing. <a href="/dashboard">Go to Dashboard</a></p></body></html>' > /app/frontend/build/index.html; \
    fi

# Copy installed Python packages from backend-builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
RUN pip install --no-cache-dir -r requirements.txt && python -m streamlit --version

# Set environment variables
ENV PYTHONPATH=/app
ENV PATH="/usr/local/bin:$PATH"
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_RUN_ON_SAVE=false
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV PORT=8080
ENV EXPRESS_PORT=3000
# Add these for proxy handling
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

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

# Create a startup script to run Express, Nginx, and Streamlit
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
# Start Nginx in the background\n\
echo "Starting Nginx..."\n\
nginx -g "daemon off;" &\n\
\n\
# Start Streamlit\n\
echo "Starting Streamlit..."\n\
python -m streamlit run src/dashboard/app.py \\\n\
    --server.port=$PORT \\\n\
    --server.address=0.0.0.0 \\\n\
    --server.baseUrlPath="dashboard" \\\n\
    --server.maxUploadSize=50 \\\n\
    --server.maxMessageSize=50 \\\n\
    --server.enableCORS=false \\\n\
    --server.enableXsrfProtection=false \\\n\
    --browser.serverPort=$PORT \\\n\
    --browser.gatherUsageStats=false\n\
' > /app/start.sh && chmod +x /app/start.sh

# Add after copying the application code
COPY alembic.ini .
COPY alembic ./alembic
COPY migrations ./migrations

# Command to run all services
CMD ["/app/start_all_services.sh"]
