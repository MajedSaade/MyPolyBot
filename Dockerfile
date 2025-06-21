# Use minimal Python image (Alpine variant)
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install system dependencies (for Python packages and runtime)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    libressl-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    libpng-dev

# Copy requirements and install Python dependencies
COPY polybot/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy full source code
COPY . .

# Command to run your app
CMD ["python", "-m", "polybot.app"]
