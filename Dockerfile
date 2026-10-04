# AERIS Backend - Root Dockerfile for Railway / Container deployments
# Stage 1: Build dependencies
FROM python:3.12.3-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.lock requirements.lock
RUN pip install --no-cache-dir --prefix=/install -r requirements.lock

# Stage 2: Runtime
FROM python:3.12.3-slim AS runtime

RUN groupadd -r aeris && useradd -r -g aeris -d /app -s /sbin/nologin aeris

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

WORKDIR /app

COPY backend/alembic/ alembic/
COPY backend/alembic.ini .
COPY backend/app/ app/
COPY backend/tests/ tests/
COPY backend/entrypoint.sh /app/entrypoint.sh

RUN mkdir -p /app/ml_artifacts /app/data && chown -R aeris:aeris /app
RUN chmod +x /app/entrypoint.sh && chown aeris:aeris /app/entrypoint.sh

USER aeris

HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=30s \
    CMD python -c "import urllib.request, os; port = os.environ.get('PORT', '8000'); urllib.request.urlopen(f'http://localhost:{port}/api/v1/health')" || exit 1

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD sh -c "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --no-access-log"
