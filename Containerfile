# Containerfile for AccessMan (Podman-compatible)
# Build with: podman build -t accessibility-manager .
# Run with: podman run -p 8765:8765 -v ./data:/data accessibility-manager

FROM python:3.12-slim

# Set environment variables for browser-only mode
ENV NICEGUI_BROWSER_ONLY=1 \
    ACCESSMAN_DB_PATH=/data/accessibility_manager.db \
    ACCESSMAN_BACKUP_DIR=/data/backups \
    ACCESSMAN_LOG_LEVEL=INFO \
    UV_SYSTEM_PYTHON=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock* ./

# Install dependencies with uv
RUN pip install uv && \
    uv pip install --system --no-cache-dir .

# Copy application
COPY accessibility_mgr/ ./accessibility_mgr/
COPY tools.ini.example tools.ini

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Create data directories
RUN mkdir -p /data/{artifacts,job_files,prints_files,backups} && \
    chown -R appuser:appuser /data

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8765/ || exit 1

# Run the application
CMD ["uv", "run", "python", "accessibility_mgr/app.py"]
