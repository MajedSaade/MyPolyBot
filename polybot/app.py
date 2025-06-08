import os
import asyncio
import threading
from dotenv import load_dotenv
from polybot.bot import ImageProcessingBot
from loguru import logger
from fastapi import FastAPI
import uvicorn
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import metrics


#majed

# Load environment variables from .env file
load_dotenv()

# Get the token from .env - try dev token first, then fall back to production token
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_DEV_BOT_TOKEN') or os.environ.get('DISCORD_BOT_TOKEN')
YOLO_URL = os.environ.get('YOLO_URL', 'http://10.0.1.90:8081/predict')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://10.0.0.136:11434/api/chat')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'gemma3:1b')
STATUS_SERVER_PORT = int(os.environ.get('STATUS_SERVER_PORT', 8443))

# Create FastAPI app for health checks
app = FastAPI()

# Register Prometheus instrumentation
Instrumentator().instrument(app).expose(app)


# Create custom meter
meter = metrics.get_meter(__name__)

# Example custom counter → you can use this in your bot logic
polybot_requests_counter = meter.create_counter("polybot_requests_total")





"For MyPolyBot check if good , old V"

@app.get("/")
def health_check():
    return {"status": "ok"}


def run_status_server():
    """Run the FastAPI status server in a separate thread"""
    logger.info(f"Starting status server on port {STATUS_SERVER_PORT}")
    try:
        uvicorn.run(app, host="0.0.0.0", port=STATUS_SERVER_PORT, log_level="info")
    except Exception as e:
        logger.error(f"Error running status server: {e}")


async def main():
    if not DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN environment variable not set")
        return

    # Start the status server in a separate thread
    status_thread = threading.Thread(target=run_status_server, daemon=True)
    status_thread.start()
    logger.info("Status server thread started")

    # Use ImageProcessingBot with YOLO URL and Ollama URL
    bot = ImageProcessingBot(DISCORD_BOT_TOKEN, YOLO_URL, OLLAMA_URL)
    logger.info("Starting Discord bot...")

    try:
        await bot.start()
    except Exception as e:
        logger.error(f"Error starting Discord bot: {e}")
    finally:
        logger.info("Discord bot stopped")


if __name__ == "__main__":
    asyncio.run(main())