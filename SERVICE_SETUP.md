# PolyBot Service Setup Guide

This guide explains how to set up and manage the PolyBot Discord service on your EC2 instance.

## Initial Setup

1. Clone the repository to your EC2 instance:
   ```bash
   git clone <your-repo-url> /home/ubuntu/MyPolyBot
   cd /home/ubuntu/MyPolyBot
   ```

2. Run the deployment script:
   ```bash
   chmod +x deploy.sh
   DISCORD_BOT_TOKEN=your_actual_token ./deploy.sh
   ```

   Or for development:
   ```bash
   chmod +x deploy-dev.sh
   DISCORD_BOT_TOKEN=your_dev_token ./deploy-dev.sh
   ```

## Environment Configuration

The deployment script automatically creates a `.env` file with the following structure:
```bash
DISCORD_BOT_TOKEN=your_discord_token_here
DISCORD_DEV_BOT_TOKEN=your_dev_token_here  # For dev environment
YOLO_URL=http://10.0.1.90:8081/predict
OLLAMA_URL=http://10.0.0.136:11434/api/chat
OLLAMA_MODEL=gemma3:1b
STATUS_SERVER_PORT=8443
AWS_REGION=us-west-2
AWS_DEV_S3_BUCKET=majed-dev-bucket
```

## Managing the Service

### Checking Service Status
```bash
sudo systemctl status polybot.service          # Production
sudo systemctl status polybot-dev.service      # Development
```

### Viewing Logs
```bash
sudo journalctl -u polybot.service -f          # Production
sudo journalctl -u polybot-dev.service -f      # Development
```

### Starting/Stopping the Service
```bash
sudo systemctl start polybot.service           # Production
sudo systemctl stop polybot.service
sudo systemctl start polybot-dev.service       # Development
sudo systemctl stop polybot-dev.service
```

### Restarting the Service
```bash
sudo systemctl restart polybot.service         # Production
sudo systemctl restart polybot-dev.service     # Development
```

## Troubleshooting

### If the Service Fails to Start
1. Check the logs for errors:
   ```bash
   sudo journalctl -u polybot.service -e
   ```

2. Verify your environment variables in `.env`:
   ```bash
   cat .env
   ```
   
3. Ensure your virtual environment has all required dependencies:
   ```bash
   source .venv/bin/activate
   pip install -r polybot/requirements.txt
   ```

### Updating the Service After Code Changes
```bash
git pull
./deploy.sh  # or ./deploy-dev.sh for development
``` 