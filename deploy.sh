#!/bin/bash

set -e  # Exit on any error

echo "Starting deployment of PolyBot..."

# Configuration
SERVICE_NAME=polybot.service
SERVICE_PATH=/etc/systemd/system/$SERVICE_NAME
APP_DIR=$(pwd)
VENV_PATH="$APP_DIR/.venv"  # Use .venv (best practice for project-local venv)

# Optional: clean pip and apt cache to save disk space
echo "Cleaning pip and apt cache..."
pip cache purge || true
sudo apt-get clean

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip wget

# Install OpenTelemetry Collector
echo "Cleaning up old otelcol .deb files..."
rm -f ~/otelcol_0.127.0_linux_amd64.deb*

echo "Installing OpenTelemetry Collector..."
wget https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.127.0/otelcol_0.127.0_linux_amd64.deb
sudo dpkg -i otelcol_0.127.0_linux_amd64.deb

echo "Configuring OpenTelemetry Collector..."
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

echo "Enabling and restarting otelcol service..."
sudo systemctl daemon-reload
sudo systemctl enable otelcol
sudo systemctl restart otelcol

# Setup Python virtual environment
echo "Setting up Python virtual environment..."
if [ -d "$VENV_PATH" ] && [ ! -f "$VENV_PATH/bin/activate" ]; then
  echo "Found incomplete virtual environment, removing it..."
  rm -rf "$VENV_PATH"
fi

if [ ! -d "$VENV_PATH" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_PATH"

  if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "❌ Failed to create virtual environment properly."
    exit 1
  fi
fi

echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

if [ -z "$VIRTUAL_ENV" ]; then
  echo "❌ Failed to activate virtual environment."
  exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip

echo "Installing critical packages..."
pip install python-dotenv fastapi uvicorn loguru discord.py

echo "Installing all requirements..."
pip install -r "$APP_DIR/polybot/requirements.txt"

# Set environment variables
echo "Setting up environment variables..."
cat > "$APP_DIR/.env" << EOL
DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN:-your_discord_token_here}
YOLO_URL=http://10.0.1.90:8081/predict
OLLAMA_URL=http://10.0.0.136:11434/api/chat
OLLAMA_MODEL=gemma3:1b
STATUS_SERVER_PORT=8443
AWS_REGION=us-west-2
AWS_DEV_S3_BUCKET=majed-bot-bucket
EOL

chmod 600 "$APP_DIR/.env"

# Display current environment settings
echo "Current environment variables:"
echo "DISCORD_BOT_TOKEN: $(if grep -q "DISCORD_BOT_TOKEN=" "$APP_DIR/.env" && [ "$(grep "DISCORD_BOT_TOKEN=" "$APP_DIR/.env" | cut -d= -f2)" != "your_discord_token_here" ]; then echo "is set"; else echo "not set"; fi)"
echo "YOLO_URL: $(grep "YOLO_URL=" "$APP_DIR/.env" | cut -d= -f2)"
echo "OLLAMA_URL: $(grep "OLLAMA_URL=" "$APP_DIR/.env" | cut -d= -f2)"

# Create systemd service
echo "Preparing systemd service file..."
sudo tee $SERVICE_PATH > /dev/null << EOL
[Unit]
Description=Discord PolyBot Service
After=network.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$APP_DIR
ExecStart=$VENV_PATH/bin/python -m polybot.app
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOL

# Test the application initialization for 5 seconds max
echo "Testing the app startup (will timeout after 5 seconds)..."
timeout 5s python -m polybot.app --test-run || {
  if [ $? -eq 124 ]; then
    echo "✅ Test run timeout reached - this is expected, the app started successfully."
  else
    echo "❌ The app failed to start when run directly."
    exit 1
  fi
}

# Deactivate the virtual environment
deactivate

# Reload daemon and restart the service
echo "Restarting PolyBot service..."
sudo systemctl daemon-reload
sudo systemctl restart $SERVICE_NAME
sudo systemctl enable $SERVICE_NAME

# Check if the service is active
if ! systemctl is-active --quiet $SERVICE_NAME; then
  echo "❌ Service failed to start"
  sudo systemctl status $SERVICE_NAME --no-pager
  sudo journalctl -u $SERVICE_NAME -n 50 --no-pager
  exit 1
else
  echo "✅ PolyBot service is running successfully."
  echo "View logs with: sudo journalctl -u $SERVICE_NAME -f"
fi

echo "Deployment completed successfully!"
