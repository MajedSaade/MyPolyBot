#!/bin/bash

set -e  # Exit on any error

# Configuration
SERVICE_NAME=polybot.service
SERVICE_PATH=/etc/systemd/system/$SERVICE_NAME
APP_DIR=/home/ubuntu/MyPolyBot
VENV_PATH=$APP_DIR/.venv

echo "🚀 Starting Polybot deployment..."

# Create directories if they don't exist
echo "📁 Creating necessary directories..."
sudo mkdir -p $(dirname $SERVICE_PATH)

# Install Python and required packages if needed
if ! command -v python3 &>/dev/null; then
    echo "🐍 Installing Python3..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# Stop and disable existing service if it exists
echo "🛑 Managing existing service..."
if systemctl list-units --full -all | grep -Fq "$SERVICE_NAME"; then
    echo "Found existing $SERVICE_NAME, stopping and disabling..."
    sudo systemctl stop $SERVICE_NAME || true
    sudo systemctl disable $SERVICE_NAME || true
else
    echo "No existing service found."
fi

# Remove old service file if it exists
if [ -f "$SERVICE_PATH" ]; then
    echo "🗑️ Removing old service file..."
    sudo rm -f $SERVICE_PATH
fi

# Clean up virtual environment for fresh install
if [ -d "$VENV_PATH" ]; then
    echo "🧹 Cleaning up old virtual environment..."
    rm -rf $VENV_PATH
fi

# Setup fresh virtual environment
echo "🔧 Setting up fresh Python virtual environment..."
python3 -m venv $VENV_PATH

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies..."
$VENV_PATH/bin/pip install --upgrade pip
$VENV_PATH/bin/pip install -r $APP_DIR/polybot/requirements.txt

# Copy the new service file
echo "⚙️ Installing new service file..."
sudo cp $APP_DIR/$SERVICE_NAME $SERVICE_PATH
sudo chmod 644 $SERVICE_PATH

# Reload systemd configuration
echo "🔄 Reloading systemd configuration..."
sudo systemctl daemon-reload

# Enable and start the new service
echo "▶️ Starting new service..."
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Wait for service to start
echo "⏳ Waiting for service to initialize..."
sleep 5

# Check if the service is running
echo "🔍 Verifying service status..."
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ $SERVICE_NAME deployed and running successfully!"
    echo "📊 Service Status:"
    sudo systemctl status $SERVICE_NAME --no-pager --lines=10
    echo ""
    echo "📝 To view logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "🔄 To restart: sudo systemctl restart $SERVICE_NAME"
    echo "🛑 To stop: sudo systemctl stop $SERVICE_NAME"
else
    echo "❌ $SERVICE_NAME failed to start!"
    echo "🔍 Service status:"
    sudo systemctl status $SERVICE_NAME --no-pager
    echo ""
    echo "📝 Recent logs:"
    sudo journalctl -u $SERVICE_NAME --no-pager --lines=20
    exit 1
fi

echo "🎉 Deployment completed successfully!"