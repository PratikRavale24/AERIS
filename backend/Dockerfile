# AERIS Backend - Multi-stage build
# Stage 1: Build dependencies
FROM python:3.12.3-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.lock .
RUN pip install --no-cache-dir --prefix=/install -r requirements.lock

# Stage 2: Runtime
FROM python:3.12.3-slim AS runtime

# Create non-root user
RUN groupadd -r aeris && useradd -r -g aeris -d /app -s /sbin/nologin aeris

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application code
COPY alembic/ alembic/
COPY alembic.ini .
COPY app/ app/
COPY tests/ tests/

# Create necessary directories
RUN mkdir -p /app/ml_artifacts && chown -R aeris:aeris /app

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && chown aeris:aeris /app/entrypoint.sh

USER aeris

# Health check
HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=30s \
    CMD python -c "import urllib.request, os; port = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/api/v1/health')" || exit 1

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD sh -c "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --no-access-log"
