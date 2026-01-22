# =============================================================================
# probablyprofit - AI Trading Bot for Prediction Markets
# Multi-stage Dockerfile for production deployment
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build React Frontend
# -----------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend files
COPY frontend/package*.json ./
RUN npm ci --silent

COPY frontend/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Python Runtime
# -----------------------------------------------------------------------------
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
        fastapi \
        uvicorn[standard] \
        jinja2 \
        openai \
        google-generativeai \
        pytrends

# Copy application code
COPY probablyprofit/ ./probablyprofit/

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app/probablyprofit/web/static ./probablyprofit/web/static/

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose web dashboard port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/status || exit 1

# Default command - can be overridden
CMD ["python", "-m", "probablyprofit.main", "--dry-run"]
