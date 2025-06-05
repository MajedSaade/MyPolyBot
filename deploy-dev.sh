#!/bin/bash

set -e  # Exit on any error

echo "Starting deployment of PolyBot (Dev)..."

# Configuration
SERVICE_NAME=polybot-dev.service
SERVICE_PATH=/etc/systemd/system/$SERVICE_NAME
APP_DIR=$(pwd)
VENV_PATH="$APP_DIR/.venv"

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip

# Remove existing virtual environment if it exists but is broken
if [ -d "$VENV_PATH" ] && [ ! -f "$VENV_PATH/bin/pip" ]; then
    echo "Removing broken virtual environment..."
    rm -rf "$VENV_PATH"
fi

# Setup virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
    
    # Verify the virtual environment was created properly
    if [ ! -f "$VENV_PATH/bin/pip" ]; then
        echo "❌ Failed to create virtual environment properly"
        exit 1
    fi
    echo "✅ Virtual environment created successfully"
fi

# Install dependencies
echo "Installing dependencies..."
"$VENV_PATH/bin/pip" install --upgrade pip

# Install critical dependencies first
echo "Installing critical dependencies..."
"$VENV_PATH/bin/pip" install python-dotenv fastapi uvicorn loguru discord.py

# Install all requirements from requirements.txt
echo "Installing all requirements..."
if ! "$VENV_PATH/bin/pip" install -r "$APP_DIR/polybot/requirements.txt"; then
    echo "❌ Failed to install requirements"
    exit 1
fi

echo "✅ All dependencies installed successfully"

# Create .env file
echo "Setting up environment configuration..."
cat > "$APP_DIR/.env" << EOL
# Discord Bot Configuration
DISCORD_DEV_BOT_TOKEN=${DISCORD_BOT_TOKEN:-your_discord_token_here}

# Services Configuration
YOLO_URL=http://10.0.1.90:8081/predict
OLLAMA_URL=http://10.0.0.136:11434/api/chat
OLLAMA_MODEL=gemma3:1b
STATUS_SERVER_PORT=8443

# AWS S3 Configuration
AWS_REGION=us-west-2
AWS_DEV_S3_BUCKET=majed-dev-bucket
EOL

chmod 600 "$APP_DIR/.env"

# Create systemd service file
echo "Setting up systemd service..."
sudo tee $SERVICE_PATH > /dev/null << EOL
[Unit]
Description=Discord Polybot Service (Dev)
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

# Start the service
echo "Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

# Check status
echo "Checking service status..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ PolyBot (Dev) deployed and running successfully!"
else
    echo "❌ Service failed to start. Check logs with: sudo journalctl -u $SERVICE_NAME"
    exit 1
fi

echo "View logs with: sudo journalctl -u $SERVICE_NAME -f"