# PolyBot Service Setup Guide

This guide explains how to set up and manage the PolyBot Discord service on your EC2 instance.

## Initial Setup

1. Clone the repository to your EC2 instance:
   ```bash
   git clone <your-repo-url> /home/ubuntu/MyPolyBot
   cd /home/ubuntu/MyPolyBot
   ```

2. Configure your environment variables by creating a `.env` file:
   ```bash
   cat > .env << EOF
   DISCORD_BOT_TOKEN=your_discord_token_here
   YOLO_URL=http://10.0.1.90:8081/predict
   OLLAMA_URL=http://10.0.1.33:11434/api/chat
   OLLAMA_MODEL=gemma3:1b
   STATUS_SERVER_PORT=8443
   EOF
   ```

3. Run the deploy script:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

## Managing the Service

### Checking Service Status
```bash
sudo systemctl status polybot.service
```

### Viewing Logs
```bash
sudo journalctl -u polybot.service -f
```

### Starting/Stopping the Service
```bash
sudo systemctl start polybot.service
sudo systemctl stop polybot.service
```

### Restarting the Service
```bash
sudo systemctl restart polybot.service
```

## Troubleshooting

### If the Service Fails to Start
1. Check the logs for errors:
   ```bash
   sudo journalctl -u polybot.service -e
   ```

2. Verify your environment variables in `/etc/systemd/system/polybot.service`:
   ```bash
   sudo nano /etc/systemd/system/polybot.service
   ```
   
3. Ensure your Python virtual environment has all required dependencies:
   ```bash
   source .venv/bin/activate
   pip install -r polybot/requirements.txt
   pip install python-dotenv fastapi uvicorn
   ```

### Updating the Service After Code Changes
```bash
git pull
./deploy.sh
``` 