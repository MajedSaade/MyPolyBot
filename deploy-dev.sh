#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting deployment of development bot service..."

# Configuration
SERVICE_NAME="polybot-dev.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"
APP_DIR="/home/ubuntu/MyPolyBot"
PYTHON_VERSION="python3"
REQUIREMENTS_PATH="$APP_DIR/polybot/requirements.txt"

# ----- Basic system setup -----
echo "📦 Updating package lists and installing dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv curl wget git

# ----- Create Python virtual environment -----
echo "🐍 Setting up Python environment..."
# Ensure we're in the app directory
cd $APP_DIR

# Clean any existing virtual environment
if [ -d ".venv" ]; then
  echo "Removing existing virtual environment..."
  rm -rf .venv
fi

# Create fresh virtual environment
echo "Creating new virtual environment..."
$PYTHON_VERSION -m venv .venv

# Verify Python is installed in the virtual environment
if [ ! -f ".venv/bin/python" ] && [ ! -f ".venv/bin/python3" ]; then
  echo "❌ Virtual environment setup failed. Exiting."
  exit 1
fi

# ----- Install pip explicitly -----
echo "🔧 Installing pip in virtual environment..."
# Method 1: Use ensurepip
.venv/bin/python -m ensurepip --upgrade

# Method 2: If method 1 fails, use get-pip.py
if [ ! -f ".venv/bin/pip" ] && [ ! -f ".venv/bin/pip3" ]; then
  echo "Using get-pip.py as fallback..."
  curl -s https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
  .venv/bin/python /tmp/get-pip.py --force-reinstall
  rm -f /tmp/get-pip.py
fi

# Determine pip executable path
if [ -f ".venv/bin/pip" ]; then
  PIP_PATH=".venv/bin/pip"
elif [ -f ".venv/bin/pip3" ]; then
  PIP_PATH=".venv/bin/pip3"
else
  echo "❌ Pip installation failed. Exiting."
  exit 1
fi

# ----- Install Python dependencies -----
echo "📚 Installing Python dependencies..."
# Update pip itself first
$PIP_PATH install --upgrade pip setuptools wheel

# Install dependencies
if [ -f "$REQUIREMENTS_PATH" ]; then
  echo "Installing project requirements..."
  $PIP_PATH install -r "$REQUIREMENTS_PATH"
else
  echo "⚠️ Requirements file not found at $REQUIREMENTS_PATH"
  exit 1
fi

# Install additional dependencies
echo "Installing additional dependencies..."
$PIP_PATH install python-dotenv fastapi uvicorn

# ----- Setup systemd service -----
echo "🔄 Setting up systemd service..."
if [ -f "$APP_DIR/$SERVICE_NAME" ]; then
  echo "Installing service file..."
  sudo cp "$APP_DIR/$SERVICE_NAME" "$SERVICE_PATH"
  sudo chmod 644 "$SERVICE_PATH"
else
  echo "❌ Service file not found at $APP_DIR/$SERVICE_NAME"
  exit 1
fi

# ----- Start and enable service -----
echo "🚦 Starting and enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

# ----- Check service status -----
echo "🔍 Checking service status..."
sleep 3  # Give the service a moment to start

if systemctl is-active --quiet "$SERVICE_NAME"; then
  echo "✅ $SERVICE_NAME is running successfully!"
else
  echo "❌ $SERVICE_NAME failed to start. Checking logs..."
  sudo systemctl status "$SERVICE_NAME" --no-pager
  echo "Full logs available with: sudo journalctl -u $SERVICE_NAME"
  exit 1
fi

echo "✨ Deployment completed successfully! ✨"
echo "View logs with: sudo journalctl -u $SERVICE_NAME -f"
