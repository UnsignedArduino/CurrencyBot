import logging
from pathlib import Path
from random import randint

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
TOKEN = load_env_var("BOT_TOKEN")
BOT_ID = int(load_env_var("BOT_ID"))
DB_URI = load_env_var("DB_URI")
DB_NAME = load_env_var("DB_NAME")
CURRENCY_NAME = load_env_var("CURRENCY_NAME")
CURRENCY_NAME_PLURAL = load_env_var("CURRENCY_NAME_PLURAL")
RAW_SCOPE = load_env_var("BOT_SCOPE")
SCOPE = int(RAW_SCOPE) if RAW_SCOPE else MISSING
if SCOPE is not MISSING:
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

BET_COIN_FLIP_CHANCE = int(load_env_var("BET_COIN_FLIP_CHANCE"))
BET_COIN_FLIP_REWARD = float(load_env_var("BET_COIN_FLIP_REWARD"))
BET_DICE_ROLL_CHANCE = int(load_env_var("BET_DICE_ROLL_CHANCE"))
BET_DICE_ROLL_REWARD = float(load_env_var("BET_DICE_ROLL_REWARD"))

GITHUB_URL = "https://github.com/UnsignedArduino/CurrencyBot"


def currency_naming(value: int) -> str:
    """
    Return the currency name plural or singular depending on the value.

    :param value: The amount.
    :return: A string which is the currency name.
    """
    return CURRENCY_NAME if value == 1 else CURRENCY_NAME_PLURAL


def random_chance(chance: int) -> bool:
    if chance < 0:
        raise ValueError(f"Chance cannot be less then 0! (Got: {chance})")
    if chance > 100:
        raise ValueError(f"Chance cannot be greater then 100! (Got: {chance})")
    return randint(1, 100) <= chance


bot = Client(token=TOKEN)
db = DBClient(uri=DB_URI, db_name=DB_NAME)


@bot.command(name="github",
             description="Shows the link to my GitHub repository!",
             scope=SCOPE)
async def github(ctx: CommandContext):
    button = Button(style=ButtonStyle.LINK,
                    label="Click to open!",
                    url=GITHUB_URL)
    embed = Embed(title="GitHub repository link",
                  description=GITHUB_URL)
    await ctx.send(embeds=embed, components=[button])


@bot.command(name="balance",
             description="Gets how much money you or another user has!",
             scope=SCOPE,
             options=[
                Option(
                    type=OptionType.USER,
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
    if member_id == BOT_ID:
        embed = Embed(description=f"<@{member_id}> has infinite "
                                  f"{CURRENCY_NAME_PLURAL}")
    else:
        embed = Embed(description=f"<@{member_id}> has {user_bal} "
                                  f"{currency_naming(user_bal)}")
    await ctx.send(embeds=embed)


@bot.command(name="claim",
             description="Claim your hourly, daily, or monthly!",
             scope=SCOPE,
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
             scope=SCOPE,
             options=[
                 Option(
                     type=OptionType.USER,
                     name="member",
                     description="The member to send coins to!",
                     required=True
                 ),
                 Option(
                     type=OptionType.INTEGER,
                     name="amount",
                     description="How much to send!",
                     min_value=1,
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
    elif to_id == BOT_ID:
        embed = Embed(description=f"I'm flattered! :flushed: But you can't "
                                  f"send me money. :cry:",
                      color=0xFF0000)
    elif amount > from_bal:
        embed = Embed(description=f"You do not have enough "
                                  f"{CURRENCY_NAME_PLURAL} to send!\n"
                                  f"(You have {from_bal} "
                                  f"{currency_naming(from_bal)} which is "
                                  f"{amount - from_bal} less then {amount})",
                      color=0xFF0000)
    else:
        await db.change_balance(member_id=from_id, change=-amount)
        await db.change_balance(member_id=to_id, change=amount)
        embed = Embed(description=f"Successfully sent <@{to_id}> "
                                  f"{amount} {currency_naming(amount)}!")
    await ctx.send(embeds=embed)


@bot.command(name="bet_coin_flip",
             description="Bet on a coin flip!",
             scope=SCOPE,
             options=[
                 Option(
                     type=OptionType.INTEGER,
                     name="amount",
                     description="How much to bet!",
                     min_value=1,
                     required=True
                 ),
                 Option(
                     type=OptionType.STRING,
                     name="side",
                     description="Side to bet on!",
                     required=True,
                     choices=[
                         {"name": "heads", "value": "heads"},
                         {"name": "tails", "value": "tails"}
                     ]
                 )
             ])
async def bet_coin_flip(ctx: CommandContext, amount: int, side: str):
    member_id = int(str(ctx.author.user.id))
    from_bal = await db.get_balance(member_id=member_id)
    if amount > from_bal:
        embed = Embed(description=f"You do not have enough "
                                  f"{CURRENCY_NAME_PLURAL} to bet!\n"
                                  f"(You have {from_bal} "
                                  f"{currency_naming(from_bal)} which is "
                                  f"{amount - from_bal} less then {amount})",
                      color=0xFF0000)
    else:
        await db.change_balance(member_id=member_id, change=-amount)
        if random_chance(BET_COIN_FLIP_CHANCE):
            got = round(amount * BET_COIN_FLIP_REWARD)
            await db.change_balance(member_id=member_id, change=got)
            embed = Embed(description=f"It was {side}! You get {got} "
                                      f"{currency_naming(got)}!")
        else:
            opposite_side = {"heads": "tails", "tails": "heads"}
            embed = Embed(description=f"It was {opposite_side[side]}! "
                                      f":pensive:")
    await ctx.send(embeds=embed)


bot.start()
