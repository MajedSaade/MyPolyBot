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
echo "Ensuring Python and dependencies are installed..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv

# Remove existing virtual environment if it exists
if [ -d "$VENV_PATH" ]; then
    echo "Removing existing virtual environment..."
    rm -rf $VENV_PATH
fi

# Create fresh virtual environment
echo "Creating virtual environment..."
python3 -m venv $VENV_PATH

# Check if virtual environment was created successfully
if [ ! -f "$VENV_PATH/bin/python" ]; then
    echo "Failed to create virtual environment. Trying alternate method..."
    python3 -m venv --without-pip $VENV_PATH
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $VENV_PATH/bin/python get-pip.py
    rm get-pip.py
fi

# Activate and install/update all dependencies
echo "Installing/updating dependencies..."
source $VENV_PATH/bin/activate
pip install --upgrade pip
pip install -r $APP_DIR/polybot/requirements.txt
pip install python-dotenv fastapi uvicorn
deactivate

# Copy the service file
echo "Installing service file..."
sudo cp $APP_DIR/$SERVICE_NAME $SERVICE_PATH
sudo chmod 644 $SERVICE_PATH

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
