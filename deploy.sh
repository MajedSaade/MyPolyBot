#!/bin/bash

set -e  # Exit on any error

# Configuration
SERVICE_NAME=polybot.service
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
fi

# Setup virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_PATH
    $VENV_PATH/bin/pip install --upgrade pip
    $VENV_PATH/bin/pip install -r $APP_DIR/polybot/requirements.txt
    $VENV_PATH/bin/pip install python-dotenv fastapi uvicorn
fi

# Create .env file if it doesn't exist or update it
echo "Setting up environment configuration..."
cat > $APP_DIR/.env << EOL
# Discord Bot Configuration
DISCORD_BOT_TOKEN=${DISCORD_TOKEN:-your_discord_token_here}

# Services Configuration  
YOLO_URL=http://10.0.1.90:8081/predict
OLLAMA_URL=http://10.0.0.136:11434/api/chat
OLLAMA_MODEL=gemma3:1b
STATUS_SERVER_PORT=8443

# AWS S3 Configuration (using IAM role for authentication)
AWS_REGION=us-west-2
AWS_DEV_S3_BUCKET=majed-dev-bucket
EOL

# Set proper permissions for .env file
chmod 600 $APP_DIR/.env

# Check if DISCORD_TOKEN environment variable is set
if [ -n "$DISCORD_TOKEN" ]; then
    echo "Using Discord token from environment variable..."
    # Replace placeholder in service file
    sed -i "s/placeholder_token_replace_this/$DISCORD_TOKEN/g" $SERVICE_NAME
fi

# Check if IAM role is attached to the instance
echo "Checking IAM role configuration..."
if curl -s -f --max-time 5 http://169.254.169.254/latest/meta-data/iam/security-credentials/ > /dev/null; then
  ROLE_NAME=$(curl -s --max-time 5 http://169.254.169.254/latest/meta-data/iam/security-credentials/)
  if [ -n "$ROLE_NAME" ]; then
    echo "✅ IAM role attached to instance: $ROLE_NAME"
    echo "S3 operations will use IAM role for authentication."
  else
    echo "⚠️ WARNING: No IAM role found attached to this instance."
  fi
else
  echo "⚠️ WARNING: Could not check IAM role status. Instance might not have an IAM role attached."
fi

# Copy the service file
echo "Installing service file..."
sudo cp $SERVICE_NAME $SERVICE_PATH
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
