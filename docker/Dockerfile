# Use slim instead of alpine for better compatibility with scientific packages
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create directories for data and logs
RUN mkdir -p /app/data/models /app/logs

# Copy application code
COPY src/ ./src/
COPY static/ ./static/

# Set environment variables for model storage
ENV SENTENCE_TRANSFORMERS_HOME=/app/data/models
ENV TRANSFORMERS_CACHE=/app/data/models
ENV HF_HOME=/app/data/models
ENV TORCH_HOME=/app/data/models

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8000/api || exit 1

# Run application
CMD ["python", "src/main.py"]
