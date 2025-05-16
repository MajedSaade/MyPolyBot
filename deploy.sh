#!/bin/bash

# Adjust this if your service has a different name
SERVICE_NAME=polybot.service

# Copy the service file (make sure it's included in the repo)
sudo cp $SERVICE_NAME /etc/systemd/system/

# Reload systemd and restart the bot service
sudo systemctl daemon-reload
sudo systemctl restart $SERVICE_NAME
sudo systemctl enable $SERVICE_NAME

# Check if the service is running
if ! systemctl is-active --quiet $SERVICE_NAME; then
  echo "❌ $SERVICE_NAME is not running."
  sudo systemctl status $SERVICE_NAME --no-pager
  exit 1
fi

echo "✅ $SERVICE_NAME deployed and running."
