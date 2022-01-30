import logging
from pathlib import Path

from dotenv import load_dotenv
from interactions import Client, CommandContext, Embed, Member, Option, \
    OptionType

from util.db import DBClient
from util.environ import load_env_var
from util.logger import create_logger

logger = create_logger(name=__name__, level=logging.DEBUG)

dotenv_path = Path.cwd() / ".env"
logger.debug(f"Loading token from {dotenv_path}")

load_dotenv(dotenv_path=dotenv_path)
token = load_env_var("BOT_TOKEN")
db_uri = load_env_var("DB_URI")
db_name = load_env_var("DB_NAME")
currency_name = load_env_var("CURRENCY_NAME")
currency_name_plural = load_env_var("CURRENCY_NAME_PLURAL")

bot = Client(token=token)
db = DBClient(uri=db_uri, db_name=db_name)


@bot.command(name="balance",
             description="Gets how much money you or another user has!",
             scope=702979262906368040,
             options=[
                Option(
                    type=OptionType.MENTIONABLE,
                    name="member",
                    description="The member to check! (Defaults to yourself)"
                )
             ])
async def balance(ctx: CommandContext, member: str = None):
    if member is None:
        member_id = int(str(ctx.author.user.id))
    else:
        member_id = int(member)
    user_bal = await db.get_balance(member_id)
    if user_bal == 1:
        text = f"<@{member_id}> has {user_bal} {currency_name}"
    else:
        text = f"<@{member_id}> has {user_bal} {currency_name_plural}"
    embed = Embed(description=text)
    await ctx.send(embeds=embed)


bot.start()
