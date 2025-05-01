import os
import asyncio
from dotenv import load_dotenv
from bot import ImageProcessingBot
from loguru import logger

# Load environment variables from .env file
load_dotenv()

# Get the token from .env
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')

async def main():
    if not DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN environment variable not set")
        return

    # Use ImageProcessingBot (make sure bot.py has the correct class)
    bot = ImageProcessingBot(DISCORD_BOT_TOKEN)

    logger.info("Starting Discord bot...")
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
