import logging
from os import getenv
from pathlib import Path

from dotenv import load_dotenv
from interactions import Client, CommandContext

from util.logger import create_logger
from util.db import DBClient
from util.environ import load_env_var

logger = create_logger(name=__name__, level=logging.DEBUG)

dotenv_path = Path.cwd() / ".env"
logger.debug(f"Loading token from {dotenv_path}")

load_dotenv(dotenv_path=dotenv_path)
token = load_env_var("BOT_TOKEN")
db_uri = load_env_var("DB_URI")
db_name = load_env_var("DB_NAME")

bot = Client(token=token)
db = DBClient(uri=db_uri, db_name=db_name)


@bot.command(name="test", description="testing")
async def test(ctx: CommandContext):
    await ctx.send("test")


bot.start()
