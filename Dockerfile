# Use minimal Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (required for some packages, TLS, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY polybot/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy full source
COPY . .

# ARG for environment (default production)
ARG ENVIRONMENT=production
ENV ENVIRONMENT=$ENVIRONMENT

# Command to run your app
CMD ["python", "app.py"]
