# CurrencyBot
A Discord bot to run an economy written in Python with 
[interactions.py](https://github.com/interactions-py/library)!

## Install
1. Ensure you are running [Python 3.9](https://www.python.org/downloads/) or 
   higher. (Only tested on 3.9)
2. Install the 
   [MongoDB community server](https://www.mongodb.com/try/download/community). 
3. Clone the repo.
4. Create a Discord application and a Discord bot.
5. Generate an OAuth2 URL to invite your bot to a server. (Make sure the bot 
   has `bot` and `applications.commands` scopes!)
6. Install dependencies in 
   [`requirements.txt`](https://github.com/UnsignedArduino/CurrencyBot/blob/main/requirements.txt).
7. Fill in the contents of 
   [`example.env`](https://github.com/UnsignedArduino/CurrencyBot/blob/main/example.env)
   and rename it to `.env`.

## Run
1. Run [`main.py`](https://github.com/UnsignedArduino/CurrencyBot/blob/main/src/main.py) 
   in the 
   [`src`](https://github.com/UnsignedArduino/CurrencyBot/tree/main/src) directory. 

## Command overview
```text
/balance (member: User)
/bet
    coin_flip <amount: Integer [>= 1]> <side: String ["heads"] ^^ ["tails"]>
    dice_roll <amount: Integer [>= 1]> <side: Integer [>= 1] && [<= 6]>
    wheel <amount: Integer [>= 1]>
/claim
    hourly
    daily
    monthly
/github
/send <member: User> <amount: Integer >= 1>
```
```text
/       denotes slash command
<tab>   denotes sub command

<>      denotes required arguments
()      denotes optional arguments

[]      denotes condition
&&      denotes both conditions must be satisfied
||      denotes at least one condition must be satisfied
^^      denotes exactly one condition must be satisfied
```
