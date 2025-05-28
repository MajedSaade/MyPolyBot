#!/bin/bash

set -e  # Exit on any error

# Configuration
SERVICE_NAME=polybot-dev.service
SERVICE_PATH=/etc/systemd/system/$SERVICE_NAME
APP_DIR=/home/ubuntu/MyPolyBot
VENV_PATH=$APP_DIR/.venv

# Create directories if they don't exist
echo "Creating necessary directories..."
sudo mkdir -p $(dirname $SERVICE_PATH)

# Install Python and required packages if needed
if ! command -v python3 &>/dev/null; then
    echo "Installing Python3..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
else
    echo "Python3 already installed."
fi

# Ensure python3-venv is available
if ! python3 -m venv --help > /dev/null 2>&1; then
    echo "Installing python3-venv..."
    sudo apt-get install -y python3-venv
fi

# Create virtual environment if not present
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_PATH
fi

# Activate and install dependencies
echo "Installing/updating dependencies..."
$VENV_PATH/bin/pip install --upgrade pip
$VENV_PATH/bin/pip install -r $APP_DIR/polybot/requirements.txt
$VENV_PATH/bin/pip install python-dotenv fastapi uvicorn

# Install systemd service
echo "Installing service file..."
sudo cp $APP_DIR/$SERVICE_NAME $SERVICE_PATH
sudo chmod 644 $SERVICE_PATH

# Reload systemd and restart/enable service
echo "Configuring systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

# Check status
echo "Checking service status..."
if ! systemctl is-active --quiet $SERVICE_NAME; then
    echo "❌ $SERVICE_NAME failed to start. Checking logs..."
    sudo systemctl status $SERVICE_NAME --no-pager
    echo "Full logs: sudo journalctl -u $SERVICE_NAME"
    exit 1
fi

echo "✅ $SERVICE_NAME deployed and running successfully."
echo "View logs with: sudo journalctl -u $SERVICE_NAME -f"
