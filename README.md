# surgetrader
Trade on surges detected at BitTrex. this is the Python2 version that operates
with SQLite.

# Script description

Have you ever woken up, logged into BitTrex,  and saw something like this:
![](https://i.imgur.com/OHvlAAM.png)

and then you asked yourself: "what could I do to wake up to profits like this".

If so, then SurgeTrader is for you!!!

## How it works

SurgeTrader allows you to find what market(s) has had the greatest % growth over a period of time. It presumes that the coin with the greatest % gain will go up even more in the near or distant future.

# Installation

Install python-bittrex from this github instead of PyPi.
`pip install -r requirements.txt`

# Configuration

in the `src` directory, `mybittrex.ini` should have key and secret in it like so

    [api]
    key = asdfa8asdf8asdfasdf
    secret = 99asdfn8sdfjasd

# Usage
## Cron

Create 1 cron entry that downloads the market data every hour (or whatever
sample period you like) and then scans for the coin with the strongest surge and buys it.

    00 * * * * cd $ST/src/ ; $PY download.py; $PY scan.py --buy 1

Create another cron entry that sets a profit target on the successful buys

    */5 * * * * cd $ST/src/ ; $PY takeprofit.py --percent 10

# Earning Potential

Account balance = $1000

2% = 20

1% gain on 2% of the account = 20.20

therefore you are making 20 cents per trade

50 trades in a month = 10 dollars profit

10 dollars is 1% of 1000 -> 1% gain on the account

Therefore taking 50 2% trades and setting a 1% profit margin (ignoring fees)

# TODO

- Move percentage of BTC to trade on each run to config file.

- Take profit right after successful buy. There is no reason for takeprofit.py
to exist separately: just edit scan.py and have it take the profit!

# MONTHLY PROFIT SHARE

* 50% client
* 25% client buys ADSactly Community Units
* 25% goes to developer (me)

ex. 1000 profit
- 500 to you
- 250 you buy community units
- 250 goes to me

#
