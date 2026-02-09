# =============================================================================
# MULTI-STAGE DOCKERFILE FOR SANAD AEO AUDITOR
# Optimized for production with clean architecture
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Base Python Image with System Dependencies
# -----------------------------------------------------------------------------
FROM python:3.13-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client for database operations
    postgresql-client \
    # Build tools for compiling Python packages
    gcc \
    g++ \
    make \
    # Additional dependencies for crawl4ai
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Stage 2: Dependencies Installation
# -----------------------------------------------------------------------------
FROM base AS dependencies

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 3: Production Image
# -----------------------------------------------------------------------------
FROM base AS production

WORKDIR /app

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Create non-root user for security
RUN groupadd -r sanad && useradd -r -g sanad sanad

# Create necessary directories
RUN mkdir -p /var/sanad/audits \
    && chown -R sanad:sanad /var/sanad \
    && mkdir -p /app/logs \
    && chown -R sanad:sanad /app/logs

# Copy application code
COPY --chown=sanad:sanad app ./app
COPY --chown=sanad:sanad alembic.ini .

# Copy Alembic migrations
COPY --chown=sanad:sanad app/alembic ./app/alembic

# Switch to non-root user
USER sanad

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# -----------------------------------------------------------------------------
# Stage 4: Development Image (with dev tools)
# -----------------------------------------------------------------------------
FROM production AS development

USER root

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    ruff \
    ipython \
    ipdb

# Install wait-for-it script for service dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && wget -qO /usr/local/bin/wait-for-it https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x /usr/local/bin/wait-for-it \
    && rm -rf /var/lib/apt/lists/*

USER sanad

# Override with reload for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
