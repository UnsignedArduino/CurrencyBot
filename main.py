import logging
from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from interactions import Client, CommandContext

from logger import create_logger

logger = create_logger(name=__name__, level=logging.DEBUG)

dotenv_path = Path.cwd() / ".env"
logger.debug(f"Loading token from {dotenv_path}")

load_dotenv(dotenv_path=dotenv_path)
token = getenv("BOT_TOKEN")

if not token:
    logger.error("No valid token found!")
    exit(1)
else:
    logger.debug(f"Found token of length {len(token)}")

bot = Client(token=token)


@bot.command(name="test", description="testing")
async def test(ctx: CommandContext):
    await ctx.send("test")


bot.start()
