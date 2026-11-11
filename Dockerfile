# ========================================================
# Stage 1: Build stage (compile wheels and prepare venv)
# Pinned official Debian slim base
# ========================================================
FROM python:3.12.7-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install minimal build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Create virtualenv and install pinned production dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ========================================================
# Stage 2: Runtime stage (minimal, hardened, non-root)
# ========================================================
FROM python:3.12.7-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="Hotel Reservation API" \
      org.opencontainers.image.description="Cloud-native, concurrency-safe hotel reservation service" \
      org.opencontainers.image.authors="DevOps Engineering Team" \
      org.opencontainers.image.vendor="Algions AI Labs" \
      org.opencontainers.image.version="1.0.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=production

# Install curl for HEALTHCHECK and postgresql-client for CLI operations
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl postgresql-client && \
    rm -rf /var/lib/apt/lists/*

# Create dedicated non-root user and group with static UID/GID 10001
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /sbin/nologin -M appuser

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source, migrations, and scripts
COPY app/ app/
COPY migrations/ migrations/
COPY alembic.ini .
COPY scripts/ scripts/
COPY entrypoint.sh .

# Ensure entrypoint and scripts are executable, and own app directory
RUN chmod +x entrypoint.sh scripts/*.sh && \
    chown -R appuser:appgroup /app

# Switch to unprivileged non-root user
USER 10001:10001

EXPOSE 8000

# Container healthcheck hitting /ready endpoint
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ready || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-config", "None"]

