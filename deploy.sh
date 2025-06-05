#!/bin/bash

set -e  # Exit on any error
#work
echo "Starting deployment of PolyBot..."

# Configuration
SERVICE_NAME=polybot.service
SERVICE_PATH=/etc/systemd/system/$SERVICE_NAME
APP_DIR=$(pwd)  # Current directory
VENV_PATH="$APP_DIR/venv"  # Use venv for consistency

# Create directories if they don't exist
echo "Creating necessary directories..."
sudo mkdir -p $(dirname $SERVICE_PATH)

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-dev build-essential libssl-dev libffi-dev

# Install python3-venv if not already installed
if ! dpkg -l | grep -q python3-venv; then
  echo "Installing python3-venv package..."
  sudo apt-get install -y python3-venv
fi

# Remove existing venv if activation fails
if [ -d "$VENV_PATH" ] && [ ! -f "$VENV_PATH/bin/activate" ]; then
  echo "Found incomplete virtual environment, removing it..."
  rm -rf "$VENV_PATH"
fi

# Create a Python virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV_PATH"

  # Verify the virtual environment was created properly
  if [ ! -f "$VENV_PATH/bin/activate" ]; then
    echo "❌ Failed to create virtual environment properly."
    exit 1
  fi
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Verify the virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
  echo "❌ Failed to activate virtual environment."
  exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip

# Install the specific required packages first to ensure they're available
echo "Installing critical packages..."
pip install python-dotenv fastapi uvicorn loguru discord.py

# Then install all requirements
echo "Installing all requirements..."
pip install -r "$APP_DIR/polybot/requirements.txt"

# Set up environment variables
echo "Setting up environment variables..."

# Always create the .env file from scratch with proper values
echo "Creating .env configuration file..."
cat > "$APP_DIR/.env" << EOL
# Discord Bot Configuration
DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN:-your_discord_token_here}

# Services Configuration
YOLO_URL=http://10.0.1.90:8081/predict
OLLAMA_URL=http://10.0.0.136:11434/api/chat
OLLAMA_MODEL=gemma3:1b
STATUS_SERVER_PORT=8443
EOL

# Display warning if token not provided
if [ -z "$DISCORD_BOT_TOKEN" ]; then
  echo "⚠️ WARNING: No Discord bot token provided. Using placeholder value."
  echo "The bot will not work until you edit .env with a valid token and restart the service."
fi

# Display current environment settings
echo "Current environment variables:"
echo "DISCORD_BOT_TOKEN: $(if grep -q "DISCORD_BOT_TOKEN=" "$APP_DIR/.env" && [ "$(grep "DISCORD_BOT_TOKEN=" "$APP_DIR/.env" | cut -d= -f2)" != "your_discord_token_here" ]; then echo "is set"; else echo "not set"; fi)"
echo "YOLO_URL: $(grep "YOLO_URL=" "$APP_DIR/.env" | cut -d= -f2)"
echo "OLLAMA_URL: $(grep "OLLAMA_URL=" "$APP_DIR/.env" | cut -d= -f2)"

# Make sure permissions are correct for .env
chmod 600 "$APP_DIR/.env"

# Create a modified service file with correct paths
echo "Preparing service file..."
cat > /tmp/$SERVICE_NAME << EOL
[Unit]
Description=Discord Polybot Service
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

# Copy the systemd service file
echo "Setting up systemd service..."
sudo cp /tmp/$SERVICE_NAME $SERVICE_PATH
sudo chmod 644 $SERVICE_PATH
rm /tmp/$SERVICE_NAME

# Test the application initialization for 5 seconds max
echo "Testing the app startup (will timeout after 5 seconds)..."
timeout 5s python -m polybot.app --test-run || {
  # Exit code 124 means timeout occurred, which is expected and okay
  if [ $? -eq 124 ]; then
    echo "✅ Test run timeout reached - this is expected, the app started successfully."
  else
    echo "❌ The app failed to start when run directly."
  fi
}

# Deactivate the virtual environment
deactivate

# Reload daemon and restart the service
echo "Restarting service..."
sudo systemctl daemon-reload
sudo systemctl restart $SERVICE_NAME
sudo systemctl enable $SERVICE_NAME

# Check if the service is active
if ! systemctl is-active --quiet $SERVICE_NAME; then
  echo "❌ Service failed to start"
  sudo systemctl status $SERVICE_NAME --no-pager

  echo "Checking detailed logs for errors..."
  sudo journalctl -u $SERVICE_NAME -n 50 --no-pager

  exit 1
else
  echo "✅ PolyBot service is running successfully."
fi

echo "Deployment completed successfully!"
