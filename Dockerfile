# Multi-stage Dockerfile for PrunArr
# Builds a lightweight, secure container image for PrunArr media cleanup tool

# Build stage - compile and prepare the application
FROM python:3.12-slim AS builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY README.md ./

# Copy source code
COPY prunarr/ ./prunarr/

# Install the package
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Runtime stage - minimal image with only runtime dependencies
FROM python:3.12-slim

# Set labels for metadata
LABEL maintainer="Haije Ploeg <ploeg.haije@gmail.com>"
LABEL org.opencontainers.image.title="PrunArr"
LABEL org.opencontainers.image.description="Automated media library cleanup for Radarr and Sonarr based on Tautulli watch status"
LABEL org.opencontainers.image.source="https://github.com/hploeg/prunarr"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# Create non-root user for security
RUN groupadd -g 1000 prunarr && \
    useradd -u 1000 -g prunarr -s /bin/bash -m prunarr

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/prunarr /usr/local/bin/prunarr

# Create cache directory with proper permissions
RUN mkdir -p /home/prunarr/.prunarr/cache && \
    chown -R prunarr:prunarr /home/prunarr

# Switch to non-root user
USER prunarr

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    CACHE_DIR=/home/prunarr/.prunarr/cache

# Volume for cache persistence
VOLUME ["/home/prunarr/.prunarr/cache"]

# Default command - show help
ENTRYPOINT ["prunarr"]
CMD ["--help"]
