# ── Stage 1: Base image with Python 3.12 ────────────────
FROM python:3.12-slim AS builder

# Install system dependencies needed by numpy/pandas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime image (slimmer) ────────────────────
FROM python:3.12-slim

WORKDIR /app

# Copy only the installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY main.py prediction.py ./
COPY Models ./Models

# Cloud Run provides PORT env var (default 8080)
ENV PORT=8080

# Run with uvicorn (workers=1 for Cloud Run's concurrency model)
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1