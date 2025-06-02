#!/bin/bash

# Path to the .env file
ENV_FILE=/home/ubuntu/MyPolyBot/.env

# Ask for Discord token
echo "Enter your Discord bot token:"
read TOKEN

# Create or update the .env file
echo "Creating/updating .env file with Discord token..."
echo "DISCORD_BOT_TOKEN=$TOKEN" | sudo tee $ENV_FILE > /dev/null

# Set proper permissions
sudo chown ubuntu:ubuntu $ENV_FILE
sudo chmod 600 $ENV_FILE

echo "Token has been set. Restarting the service..."
sudo systemctl daemon-reload
sudo systemctl restart polybot.service

# Check status
echo "Checking service status..."
sudo systemctl status polybot.service 