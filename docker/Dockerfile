#!/usr/bin/env dockerfile
# =============================================================================
# PsychSync Production Dockerfile
# =============================================================================
#
# Multi-stage production Docker image for PsychSync platform.
#
# Features:
# - Multi-stage build (builder + runtime)
# - Non-root user execution
# - Minimal attack surface
# - Security best practices
# - Optimized for production
#
# Architecture: linux/amd64, linux/arm64
# Python Version: 3.12-slim
#
# Usage:
#   docker build -f docker/Dockerfile -t psychsync:latest .
#
# Author: DevOps Team
# Version: 2.0
# Date: 2025-12-27
# =============================================================================

# Set build arguments for reproducibility
ARG PYTHON_VERSION=3.12
ARG DEBIAN_VERSION=bookworm

# =============================================================================
# Stage 1: BUILDER
# =============================================================================
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_VERSION} AS builder

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    WORKDIR=/build

WORKDIR /build

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    libmariadb-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY app/requirements.txt .

# Install Python dependencies into /opt/venv
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /opt/venv/bin/pip install gunicorn uvicorn[standard] && \
    rm -rf /root/.cache/pip

# =============================================================================
# Stage 2: RUNTIME
# =============================================================================
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_VERSION}

# Set labels for metadata
LABEL maintainer="DevOps Team <devops@psychsync.ai>" \
      version="2.0" \
      description="PsychSync Platform Production Image" \
      org.opencontainers.image.title="PsychSync" \
      org.opencontainers.image.description="Psychological Assessment Platform" \
      org.opencontainers.image.vendor="PsychSync" \
      org.opencontainers.image.licenses="Proprietary"

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    WORKDIR=/app \
    # Security: Don't run as root
    # APP_USER=appuser \
    # APP_UID=1000 \
    # APP_GID=1000

WORKDIR /app

# Install runtime dependencies only
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        curl \
        ca-certificates \
    && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives /var/cache/debconf/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user
RUN groupadd -r appuser -g 1000 && \
    useradd -r -g appuser -u 1000 -m -s /bin/bash -c "PsychSync Application" appuser && \
    mkdir -p /app/alembic /app/logs /app/tmp && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser app /app/app
COPY --chown=appuser:appuser app/alembic /app/alembic
COPY --chown=appuser:appuser app/alembic.ini /app/

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application with Gunicorn
# Production settings:
# - 4 workers (auto-scaled based on CPU)
# - Uvicorn workers (ASGI)
# - Threaded workers
# - Graceful timeout on reload
# - Access/error logging
CMD ["gunicorn", \
     "app.main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000", \
     "--worker-tmp-dir", "/dev/shm", \
     "--worker-connections", "1000", \
     "--max-requests", "10000", \
     "--max-requests-jitter", "1000", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keepalive", "5", \
     "--access-logfile", "/app/logs/access.log", \
     "--error-logfile", "/app/logs/error.log", \
     "--log-level", "info", \
     "--capture-output", \
     "--enable-stdio-inheritance", \
     "--statsd-host", "localhost:9125"]

# =============================================================================
# Build Arguments
# =============================================================================
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Labels for OCI compliance
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.source="https://github.com/your-org/psychsync"
