import os
import asyncio
import threading
from dotenv import load_dotenv
from polybot.bot import ImageProcessingBot
from loguru import logger
from fastapi import FastAPI, Request
import uvicorn
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry import metrics

# Load correct .env file
env_file = '.env.dev' if os.environ.get('ENVIRONMENT') == 'development' else '.env'
load_dotenv(env_file)

ENVIRONMENT = os.environ.get('ENVIRONMENT', 'production')

if ENVIRONMENT == 'development':
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_DEV_BOT_TOKEN')
    YOLO_URL = os.environ.get('YOLO_URL', 'http://10.0.0.66:8081/predict')
else:
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
    YOLO_URL = os.environ.get('YOLO_URL', 'http://10.0.1.90:8081/predict')

# Common settings
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://10.0.0.136:11434/api/chat')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'gemma3:1b')
STATUS_SERVER_PORT = int(os.environ.get('STATUS_SERVER_PORT', 8443))

# Create FastAPI app
app = FastAPI()

# Instrumentation
Instrumentator().instrument(app).expose(app)
FastAPIInstrumentor.instrument_app(app)

meter = metrics.get_meter(__name__)
polybot_requests_counter = meter.create_counter("polybot_requests_total")

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/predictions/{prediction_id}")
async def receive_prediction(prediction_id: str, request: Request):
    data = await request.json()
    logger.info(f"✅ Received prediction callback for ID {prediction_id}: {data}")
    # Optional: send result to Discord user/chat here
    return {"status": "received"}

def run_status_server():
    logger.info(f"Starting status server on port {STATUS_SERVER_PORT}")
    try:
        uvicorn.run(app, host="0.0.0.0", port=STATUS_SERVER_PORT, log_level="info")
    except Exception as e:
        logger.error(f"Error running status server: {e}")

async def main():
    if not DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN environment variable not set")
        return

    status_thread = threading.Thread(target=run_status_server, daemon=True)
    status_thread.start()
    logger.info("Status server thread started")

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
