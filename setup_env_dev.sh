#!/bin/bash

set -e  # Exit on any error

# Configuration
APP_DIR=$(pwd)
VENV_PATH="$APP_DIR/venv"  # Use venv directory as in the new deploy-dev.sh

echo "Setting up environment for PolyBot (Dev)..."

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-dev build-essential libssl-dev libffi-dev

# Create virtual environment
if [ -d "$VENV_PATH" ] && [ ! -f "$VENV_PATH/bin/activate" ]; then
  echo "Found incomplete virtual environment, removing it..."
  rm -rf "$VENV_PATH"
fi

echo "Creating Python virtual environment..."
python3 -m venv "$VENV_PATH"

# Verify the virtual environment was created properly
if [ ! -f "$VENV_PATH/bin/activate" ]; then
  echo "❌ Failed to create virtual environment properly."
  exit 1
fi

# Activate the environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Verify the virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
  echo "❌ Failed to activate virtual environment."
  exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r "$APP_DIR/polybot/requirements.txt"
pip install python-dotenv fastapi uvicorn loguru discord.py

# Create default .env.dev file if it doesn't exist
if [ ! -f "$APP_DIR/.env.dev" ]; then
    echo "Creating default .env.dev file (you will need to edit this with your credentials)..."
    
    # Try to copy from .env if it exists
    if [ -f "$APP_DIR/.env" ]; then
        echo "Copying from existing .env file..."
        cp "$APP_DIR/.env" "$APP_DIR/.env.dev"
    else
        cat > "$APP_DIR/.env.dev" << EOL
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_discord_token_here

# Services Configuration
YOLO_URL=http://10.0.1.90:8081/predict
OLLAMA_URL=http://10.0.0.136:11434/api/chat
OLLAMA_MODEL=gemma3:1b
STATUS_SERVER_PORT=8443
EOL
    fi
    
    echo ".env.dev file created. Please edit it with your actual credentials."
fi

# Make sure permissions are correct
chmod 600 "$APP_DIR/.env.dev"

# Deactivate the virtual environment
deactivate

echo "✅ Dev environment setup complete! Next steps:"
echo "1. Edit the .env.dev file with your credentials"
echo "2. Run ./deploy-dev.sh to deploy the service" 