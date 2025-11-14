# Optimized multi-stage build for linux/amd64 platform
# Stage 1: Build dependencies
FROM --platform=linux/amd64 python:3.11-slim as builder

WORKDIR /app

# Install build dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set PATH early to avoid warnings
ENV PATH=/root/.local/bin:$PATH

# Copy requirements files
COPY requirements.txt requirements-no-torch.txt ./

# Use BuildKit cache mount for pip cache (faster rebuilds)
# Install torch CPU-only first (~200MB vs ~4GB with CUDA) - MUCH FASTER!
# This avoids downloading 4GB of CUDA libraries when CPU-only is sufficient
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install --user --index-url https://download.pytorch.org/whl/cpu \
    torch>=2.4.0

# Install other dependencies (torch already installed, will be skipped)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user -r requirements-no-torch.txt

# Stage 2: Runtime image (smaller and faster)
FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# Install only minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Create directories for data and logs
RUN mkdir -p /app/data/models /app/logs

# Set environment variables for model storage and performance
ENV SENTENCE_TRANSFORMERS_HOME=/app/data/models
ENV TRANSFORMERS_CACHE=/app/data/models
ENV HF_HOME=/app/data/models
ENV TORCH_HOME=/app/data/models
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy application code (this changes most frequently, so do it last)
COPY src/ ./src/
COPY static/ ./static/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8000/api || exit 1

# Run application
CMD ["python", "src/main.py"]
