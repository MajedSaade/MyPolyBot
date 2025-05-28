#!/bin/bash

set -e  # Exit on any error

# Configuration
SERVICE_NAME=polybot-dev.service
SERVICE_PATH=/etc/systemd/system/$SERVICE_NAME
APP_DIR=$(pwd)  # Use current directory instead of hardcoded path
VENV_PATH=$APP_DIR/.venv

echo "Deploying PolyBot from directory: $APP_DIR"

# Create directories if they don't exist
echo "Creating necessary directories..."
sudo mkdir -p $(dirname $SERVICE_PATH)

# Install Python and required packages if needed
if ! command -v python3 &>/dev/null; then
    echo "Installing Python3..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# Ensure python3-venv is installed for creating virtual environments
if ! python3 -m venv --help > /dev/null 2>&1; then
    echo "Installing python3-venv..."
    sudo apt-get install -y python3-venv
fi

# Setup virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    mkdir -p "$(dirname "$VENV_PATH")"
    python3 -m venv $VENV_PATH
fi

# Activate and install/update all dependencies
echo "Installing/updating dependencies..."
source $VENV_PATH/bin/activate
python -m pip install --upgrade pip
python -m pip install -r $APP_DIR/polybot/requirements.txt
python -m pip install python-dotenv fastapi uvicorn
deactivate

# Create .env.dev file if it doesn't exist
if [ ! -f "$APP_DIR/.env.dev" ]; then
    echo "Creating default .env.dev file..."
    cp -n $APP_DIR/.env $APP_DIR/.env.dev 2>/dev/null || cat > $APP_DIR/.env.dev << EOL
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_discord_token_here

# Services Configuration
YOLO_URL=http://10.0.1.90:8081/predict
OLLAMA_URL=http://10.0.0.136:11434/api/chat
OLLAMA_MODEL=gemma3:1b
STATUS_SERVER_PORT=8443
EOL
    echo ".env.dev file created. Please edit it with your actual credentials."
fi

# Copy the service file and update paths
echo "Installing service file..."
cat $APP_DIR/$SERVICE_NAME > /tmp/$SERVICE_NAME.tmp
sed -i "s|User=ubuntu|User=$(whoami)|g" /tmp/$SERVICE_NAME.tmp
sed -i "s|/home/ubuntu/MyPolyBot|$APP_DIR|g" /tmp/$SERVICE_NAME.tmp

# Install the updated service file
sudo cp /tmp/$SERVICE_NAME.tmp $SERVICE_PATH
sudo chmod 644 $SERVICE_PATH
rm /tmp/$SERVICE_NAME.tmp

# Reload systemd and restart/enable the bot service
echo "Configuring systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

# Check if the service is running
echo "Checking service status..."
if ! systemctl is-active --quiet $SERVICE_NAME; then
    echo "❌ $SERVICE_NAME failed to start. Checking logs..."
    sudo systemctl status $SERVICE_NAME --no-pager
    echo "Full logs available with: sudo journalctl -u $SERVICE_NAME"
    exit 1
fi

echo "✅ $SERVICE_NAME deployed and running successfully."
echo "View logs with: sudo journalctl -u $SERVICE_NAME -f"
