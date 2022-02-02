import logging
from pathlib import Path

import arrow
from dotenv import load_dotenv
from interactions import Client, CommandContext, Embed, Option, OptionType, \
    Button, ButtonStyle, MISSING

from util.db import DBClient
from util.environ import load_env_var
from util.logger import create_logger

logger = create_logger(name=__name__, level=logging.DEBUG)

dotenv_path = Path.cwd() / ".env"
logger.debug(f"Loading token from {dotenv_path}")

load_dotenv(dotenv_path=dotenv_path)
token = load_env_var("BOT_TOKEN")
bot_id = int(load_env_var("BOT_ID"))
db_uri = load_env_var("DB_URI")
db_name = load_env_var("DB_NAME")
currency_name = load_env_var("CURRENCY_NAME")
currency_name_plural = load_env_var("CURRENCY_NAME_PLURAL")
raw_scope = load_env_var("BOT_SCOPE")
scope = int(raw_scope) if raw_scope else MISSING
if scope is not MISSING:
    logger.warning(f"Scope has been restricted to a single server!")
else:
    logger.debug("Scope is global")

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

GITHUB_URL = "https://github.com/UnsignedArduino/CurrencyBot"


def currency_naming(value: int) -> str:
    """
    Return the currency name plural or singular depending on the value.

    :param value: The amount.
    :return: A string which is the currency name.
    """
    return currency_name if value == 1 else currency_name_plural


bot = Client(token=token)
db = DBClient(uri=db_uri, db_name=db_name)


@bot.command(name="github",
             description="Shows the link to my GitHub repository!",
             scope=scope)
async def github(ctx: CommandContext):
    button = Button(style=ButtonStyle.LINK,
                    label="Click to open!",
                    url=GITHUB_URL)
    embed = Embed(title="GitHub repository link",
                  description=GITHUB_URL)
    await ctx.send(embeds=embed, components=[button])


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
    if member_id == bot_id:
        embed = Embed(description=f"<@{member_id}> has infinite "
                                  f"{currency_name_plural}")
    else:
        embed = Embed(description=f"<@{member_id}> has {user_bal} "
                                  f"{currency_naming(user_bal)}")
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
        embed = Embed(description=f'You claimed your {sub_command} and got '
                                  f'{earned} {currency_naming(earned)}!')
    else:
        time_left = arrow.get(last_claim + CLAIM_TIMES[sub_command])
        embed = Embed(description=f"You can claim your {sub_command} in "
                                  f"{time_left.humanize(only_distance=True)}!",
                      color=0xFF0000)
    await ctx.send(embeds=embed)


@bot.command(name="send",
             description="Send people coins!",
             scope=scope,
             options=[
                 Option(
                     type=OptionType.MENTIONABLE,
                     name="member",
                     description="The member to send coins to!",
                     required=True
                 ),
                 Option(
                     type=OptionType.INTEGER,
                     name="amount",
                     description="How much to send!",
                     required=True
                 )
             ])
async def send(ctx: CommandContext, member: str, amount: int):
    from_id = int(str(ctx.author.user.id))
    to_id = int(member)
    from_bal = await db.get_balance(from_id)
    if from_id == to_id:
        embed = Embed(description=f"You can't send yourself money!",
                      color=0xFF0000)
    elif to_id == bot_id:
        embed = Embed(description=f"I'm flattered! :flushed: But you can't "
                                  f"send me money. :cry:",
                      color=0xFF0000)
    elif amount > from_bal:
        embed = Embed(description=f"You do not have enough "
                                  f"{currency_name_plural} to send!\n"
                                  f"(You have {from_bal} "
                                  f"{currency_naming(from_bal)} which is "
                                  f"{amount - from_bal} less then {amount})",
                      color=0xFF0000)
    elif amount <= 0:
        embed = Embed(description=f"You cannot send less then "
                                  f"1 {currency_name}!",
                      color=0xFF0000)
    else:
        await db.change_balance(member_id=from_id, change=-amount)
        await db.change_balance(member_id=to_id, change=amount)
        embed = Embed(description=f"Successfully sent <@{to_id}> "
                                  f"{amount} {currency_naming(amount)}!")
    await ctx.send(embeds=embed)


bot.start()
