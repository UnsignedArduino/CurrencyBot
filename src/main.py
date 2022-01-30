import logging
from pathlib import Path

import arrow
from dotenv import load_dotenv
from interactions import Client, CommandContext, Embed, Option, OptionType

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
scope = int(load_env_var("BOT_SCOPE"))

CLAIM_TIMES = {
    "hourly": 3600,
    "daily": 86400,
    "monthly": 2592000
}

CLAIM_VALUES = {
    "hourly": int(load_env_var("HOURLY_CLAIM")),
    "daily": int(load_env_var("DAILY_CLAIM")),
    "monthly": int(load_env_var("MONTHLY_CLAIM")),
}

bot = Client(token=token)
db = DBClient(uri=db_uri, db_name=db_name)


@bot.command(name="balance",
             description="Gets how much money you or another user has!",
             scope=scope,
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


@bot.command(name="claim",
             description="Claim your hourly, daily, or monthly!",
             scope=scope,
             options=[
                 Option(
                     type=OptionType.SUB_COMMAND,
                     name="hourly",
                     description="Claim your hourly! "
                                 "(Which you can do...every hour)"
                 ),
                 Option(
                     type=OptionType.SUB_COMMAND,
                     name="daily",
                     description="Claim your daily! "
                                 "(Which you can do...every day)"
                 ),
                 Option(
                     type=OptionType.SUB_COMMAND,
                     name="monthly",
                     description="Claim your monthly! "
                                 "(Which you can do every 30 day period)"
                 ),
             ])
async def claim(ctx: CommandContext, sub_command: str):
    member_id = int(str(ctx.author.user.id))
    last_claim = await db.get_last_claim(member_id=member_id,
                                          claim_type=sub_command)
    last_claim = last_claim.int_timestamp
    time_diff = CLAIM_TIMES[sub_command]
    now = arrow.now().int_timestamp
    if now - last_claim > time_diff:
        earned = CLAIM_VALUES[sub_command]
        await db.change_balance(member_id=member_id, change=earned)
        await db.set_last_claim(member_id=member_id, claim_type=sub_command,
                                last_claim_time=now)
        embed = Embed(description=f"You claimed your {sub_command} and got "
                                  f"{earned} {currency_name_plural}!")
    else:
        time_left = arrow.get(last_claim + CLAIM_TIMES[sub_command])
        embed = Embed(description=f"You can claim your {sub_command} in "
                                  f"{time_left.humanize(only_distance=True)}!",
                      color=0xFF0000)
    await ctx.send(embeds=embed)


bot.start()
