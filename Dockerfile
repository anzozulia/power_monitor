# Power Outage Monitor - Multi-stage Dockerfile
# Supports both development and production builds

# ============================================
# Base Stage - Common dependencies
# ============================================
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    postgresql-client \
    fonts-dejavu-core \
    fonts-liberation \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Development Stage
# ============================================
FROM base as development

# Install development tools
RUN pip install --no-cache-dir watchdog

# Copy scripts
COPY scripts/ ./scripts/
RUN chmod +x ./scripts/*.sh

# Copy application code
COPY src/ ./src/

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["./scripts/entrypoint.sh"]

# Default command for development
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]

# ============================================
# Production Stage
# ============================================
FROM base as production

# Create non-root user for security
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser

# Copy scripts
COPY scripts/ ./scripts/
RUN chmod +x ./scripts/*.sh

# Copy application code
COPY src/ ./src/

# Create logs directory
RUN mkdir -p /app/logs

# Change ownership to non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["./scripts/entrypoint.sh"]

# Production command with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--chdir", "src", "config.wsgi:application"]
