# Dockerfile for ML Model Training Service
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app/src

WORKDIR /app

# Install system dependencies for ML libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY data/ ./data/
COPY models/ ./models/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Health check for ML service
HEALTHCHECK --interval=60s --timeout=30s --start-period=10s --retries=2 \
    CMD python -c "import sklearn; import pandas; import numpy; exit(0)"

# Run ML model training
CMD ["python", "src/ml_models.py"]
