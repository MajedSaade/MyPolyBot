#!/bin/bash

set -e  # Exit on any error

echo "Starting deployment of PolyBot..."

# Configuration
SERVICE_NAME=polybot.service
SERVICE_PATH=/etc/systemd/system/$SERVICE_NAME
APP_DIR=$(pwd)
VENV_PATH="$APP_DIR/.venv"

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip wget

# Install OpenTelemetry Collector (core version)
wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.127.0/otelcol_0.127.0_linux_amd64.deb
sudo dpkg -i otelcol_0.127.0_linux_amd64.deb

# Configure the Collector
sudo tee /etc/otelcol/config.yaml > /dev/null << EOL
receivers:
  hostmetrics:
    collection_interval: 15s
    scrapers:
      cpu:
      memory:
      disk:
      filesystem:
      load:
      network:
      processes:

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"

service:
  pipelines:
    metrics:
      receivers: [hostmetrics]
      exporters: [prometheus]
EOL

# Restart the Collector service
sudo systemctl restart otelcol

# Remove existing virtual environment if broken
if [ -d "$VENV_PATH" ] && [ ! -f "$VENV_PATH/bin/pip" ]; then
    echo "Removing broken virtual environment..."
    rm -rf "$VENV_PATH"
fi

# Create virtual environment if not existing
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"

    if [ ! -f "$VENV_PATH/bin/pip" ]; then
        echo "❌ Failed to create virtual environment properly"
        exit 1
    fi
    echo "✅ Virtual environment created successfully"
fi

# Install dependencies
echo "Installing dependencies..."
"$VENV_PATH/bin/pip" install --upgrade pip
"$VENV_PATH/bin/pip" install python-dotenv fastapi uvicorn loguru discord.py
"$VENV_PATH/bin/pip" install -r "$APP_DIR/polybot/requirements.txt"

# Set environment variables
cat > "$APP_DIR/.env" << EOL
DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN:-your_discord_token_here}
YOLO_URL=http://10.0.1.90:8080/predict
OLLAMA_URL=http://10.0.0.136:11434/api/chat
OLLAMA_MODEL=gemma3:1b
STATUS_SERVER_PORT=8443
AWS_REGION=us-west-2
AWS_DEV_S3_BUCKET=majed-bot-bucket
EOL

chmod 600 "$APP_DIR/.env"

# Create and enable systemd service
sudo tee $SERVICE_PATH > /dev/null << EOL
[Unit]
Description=Discord Polybot Service
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$APP_DIR
ExecStart=$VENV_PATH/bin/python $APP_DIR/polybot/app.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1
Environment=PYTHONPATH=$APP_DIR
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ PolyBot deployed and running successfully!"
else
    echo "❌ Service failed to start. Check logs with: sudo journalctl -u $SERVICE_NAME"
    exit 1
fi

echo "View logs with: sudo journalctl -u $SERVICE_NAME -f"
