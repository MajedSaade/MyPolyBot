#!/bin/bash

set -e  # Exit on any error

# Configuration
APP_DIR=$(pwd)
VENV_PATH="$APP_DIR/.venv"

echo "Setting up environment for PolyBot..."

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv $VENV_PATH
source $VENV_PATH/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r $APP_DIR/polybot/requirements.txt
pip install python-dotenv fastapi uvicorn

# Create default .env file if it doesn't exist
if [ ! -f "$APP_DIR/.env" ]; then
    echo "Creating default .env file (you will need to edit this with your credentials)..."
    cat > $APP_DIR/.env << EOL
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_discord_token_here

# Services Configuration
YOLO_URL=http://10.0.1.90:8081/predict
OLLAMA_URL=http://localhost:11434/api/chat
OLLAMA_MODEL=mistral
STATUS_SERVER_PORT=8443
EOL
    echo ".env file created. Please edit it with your actual credentials."
fi

echo "✅ Environment setup complete! Next steps:"
echo "1. Edit the .env file with your credentials"
echo "2. Run ./deploy.sh to deploy the service" 