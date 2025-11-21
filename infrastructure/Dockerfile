# Multi-stage Dockerfile for Hands-Off Engine

FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    cron \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -s /bin/bash houser && \
    mkdir -p /app /var/log/hands-off-engine && \
    chown -R houser:houser /app /var/log/hands-off-engine

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    structlog \
    psutil \
    requests

# Copy application code
COPY --chown=houser:houser . /app/

# Create state directories
RUN mkdir -p /app/state /app/termux-hands-off/state && \
    chown -R houser:houser /app

USER houser

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python3 /app/infrastructure/health_monitor.py --json || exit 1

# Default command (overridden by docker-compose)
CMD ["python3", "/app/infrastructure/selfheal.py"]

# ============================================================
# Service-specific stages
# ============================================================

FROM base as selfheal
CMD ["python3", "/app/infrastructure/selfheal.py"]

FROM base as health-monitor
CMD ["python3", "/app/infrastructure/health_monitor.py", "--watch", "60", "--json"]

FROM base as orchestrator
CMD ["python3", "/app/termux-hands-off/agent/orchestrator.py"]

FROM base as pipeline
CMD ["/app/scripts/run_and_notify.sh"]
