# Multi-stage Dockerfile for Digital Twin AI
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed data/chroma models outputs

# Expose API port
EXPOSE 8000

# Default command (can be overridden)
CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000"]