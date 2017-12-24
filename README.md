# surgetrader
A python bot designed to profit on price surges detected at BitTrex.

## How does it work?

SurgeTrader finds what coin has had the greatest percent growth in price over a period
of time (typically an hour). It then buys that coin at market value and sets a profit target.

## How well has it worked?

I record performance in [this blog](https://surgetraderbot.blogspot.com/) on a daily basis.
You may ask questions in the reddit group for SurgeTrader](https://www.reddit.com/r/surgetraderbot/). 

Here are some other ways to learn about it:

* [AMA Chat on reddit cryptomarkets](https://www.reddit.com/r/CryptoMarkets/comments/7a20lc/im_the_author_the_foss_crypto_trading_bot/)
* [A comment I made](https://www.reddit.com/r/CryptoMarkets/comments/7dxyb4/bitcoin_cash_traders_lose_millions_as_exchange/dq1jeuk/) in response to a panic buy where people list millions - SurgeTraderBot can rightly be seen as a bot that sometimes buys into panic.

# How do I install this bad boy?

1. You need Python **3**. I recommend the [Miniconda](https://conda.io/miniconda.html) or [Anaconda](https://www.anaconda.com) Python 3 distribution.
1. Install python-bittrex from [this
github](https://github.com/metaperl/python-bittrex) instead of PyPi.
1. `git clone https://gitlab.com/metaperl/surgetrader/`
1. `cd surgetrader`
1. `pip install -r requirements.txt`

## Configuration

1. At the shell, copy `src/system.ini.sample` to `src/system.ini` and configure the file as documented.
1. In the `src/users` directory, create an ini file for each account that will
be trading. Follow the documentation in `src/users/sample.ini` for directions.
1. Update the variable `INIS` in the file `src/users/users.py` with the name of this new ini file.

### Optimal Settings

Over a period of experimentation, I have found that
these settings work well:

    Each trade should use 3% of the account. Aim for a 5% profit margin.

You can aim for higher profit margins if you are more interested in weekly or monthly profits. But for daily
profits, you should only aim for 2% profit.

## Cron

Create 1 cron entry that downloads the market data every hour (or whatever
sample period you like) and then scans for the coin with the strongest
surge and buys it:

    INVOKE=/home/schemelab/install/miniconda3/bin/invoke

    00   * * * * cd ~/prg/surgetrader/src/ ; $INVOKE download ; $INVOKE buy
    */5  * * * * cd ~/prg/surgetrader/src/ ; $INVOKE takeprofit
    @weekly      cd ~/prg/surgetrader/src/ ; $INVOKE cancelsells
    11   0 * * * cd ~/prg/surgetrader/src/ ; $INVOKE profitreport -d yesterday
    22   0 1 * * cd ~/prg/surgetrader/src/ ; $INVOKE profitreport -d lastmonth

### Note

What is `clearprofit`? It is a hack I put in place because Bittrex
recently decided to close all trades older than 28 days. So what
`clearprofit` does is cancel sell orders once a week and delete the
`sell_id` from the database. Then the takeprofit task will notice
that a buy trade does not have a sell limit order in place and will
automatically place a new one.

This code has not been thoroughly tested.

Some people want to set profit targets as soon as they buy instead of doing it every 5 minutes.
You can see the modifications that one individual made
[here](https://www.reddit.com/r/CryptoMarkets/comments/7a20lc/im_the_author_the_foss_crypto_trading_bot/dpbuwzw/).

## System Hygiene

### Error email: "Order closed but did not sell"

Occasionally you will get an email from SurgeTraderBot with the subject "SurgeTraderBOT aborted execution on exception"
and in the body of the email you will see something like this:

    Traceback (most recent call last):
      File "/home/schemelab/prg/surgetrader/src/lib/report/profit.py", line 263, in main
        html, total_profit = report_profit(config_file, exchange, _date)
      File "/home/schemelab/prg/surgetrader/src/lib/report/profit.py", line 150, in report_profit
        raise Exception("Order closed but did not sell: {}".format(so))
    Exception: Order closed but did not sell: {'AccountId': None, 'OrderUuid': '0a5ef35c-edde-49fe-b569-8a4c7e2f7259', 'Exchange': 'BTC-XAUR',

The reason this happens is that BitTrex delists coins without notice. So what happened is that you bought a coin and before 
you could sell it, Bittrex delisted it. So...what you must do is delete those records from the database so the error does not occur again. In this
case the COIN `XAUR` must be removed from our local database:

    schemelab@metta:~/prg/surgetrader/src$ sqlite3 storage.sqlite3
    SQLite version 3.13.0 2016-05-18 10:57:30
    Enter ".help" for usage hints.
    sqlite> SELECT * FROM buy WHERE market='BTC-XAUR';
    1639|542ceb17-cf28-436d-8291-87f0dd98900c|BTC-XAUR|3.456e-05|3.52512e-05|1446.75925925926|2017-10-19 13:00:30|agnes.ini|3cf637d7-352b-410c-adaf-32cf488964a2
    1946|36108597-bbb5-49e3-84b3-df5e25b309dd|BTC-XAUR|2.922e-05|2.98044e-05|6844.62696783025|2017-11-09 08:01:04|ini-steadyvest@protonmail.ini|4cd7c755-27f9-4ac0-9752-f25d517c17f0
    2275|77abdc33-8601-4317-8ef1-ca3f13077ada|BTC-XAUR|1.556e-05|1.6338e-05|1928.0205655527|2017-12-15 23:00:55|ini-steadyvest@protonmail.ini|0a5ef35c-edde-49fe-b569-8a4c7e2f7259
    sqlite> DELETE FROM  buy WHERE market='BTC-XAUR';
    sqlite> .exit

It's very important to run the `SELECT` statement, and then type `DELETE ` and copy and paste the text `FROM buy WHERE market='BTC-XAUR';` ...
the reason this is important is so that you do not issue the wrong `DELETE` statement and wipe your entire database.

Alternatively backup the file `storage.sqlite3` before doing this because if you don't you may regret it and my DISCLAIMER frees me from any
losses you may incur while using this code!

At that point, you can do what you want with your coin: liquidate it on Bittrex or send it somewhere else.

## Manual Usage

All usage of SurgeTrader, whether automated or manual, occurs with your current working directory set to `src`:

    shell> cd $HOME/gitclones/surgetrader/src

All usage of SurgeTrader is controlled by calling `invoke`. A very simple thing that should work is:

    shell> invoke download


# User-Level Docs (show me the money)

The first thing you need to understand is that SurgeTrader detects
surges in coins. The thing about a surging coin is that you may be
late to the party: you might be buying just as the sell-off is about
to start, which means you might not collect your profit immediately.

Sure, there are those times, where the same coin gives you 3 or 4
profits in 3 or 4 hours:
![](https://api.monosnap.com/rpc/file/download?id=8RKinNxVaGOlJCRMCgIbQY2oZlxKQT)

But sometimes you get caught out at the top of [a teacup and handle
formation](http://www.investopedia.com/terms/c/cupandhandle.asp) and it might be 3-4 weeks before a trade closes.


## The most important rules of SurgeTrader is...

YOUR ACCCOUNT WILL ALWAYS DECREASE IN ESTIMATED VALUE.

That's right. Unlike normal trading (Binary Options, Forex, Stocks,
etc), your account will be in permanent drawdown. If you deposit 1
BTC, expect your account value to plummet to 0.5 BTC and even
lower. Expect all BTC to be gone and the estimated value of the
account to hover about 0.25 BTC. And then get ready to collect small
profits every day, only to open another losing trade which will
eventually yield another small profit.

So let me give you a concrete example. Let's say that you did in fact
deposit 1 BTC to start. And let's say that you allocate 5% to each
surge detected every hour. It will only take 19 or 20 hours to drain
your account of BTC. Now you have 19 trades open. Every trade is
immediately losing because we buy the coin at a market price and the
bids will always be lower than that. So now you have 0 BTC and an
estimated account value of probably 0.9 BTC or so. And then over 24
hours [most trades lose even more value](http://take.ms/MgmwO) and now
you are really getting riled up because you do not know about [the
Emotional Market Cycle](https://www.youtube.com/watch?v=NMpVgvA5k3I)
so then you sell all your coins for a loss and try to stalk me
down... hahah.

But no, on average you will find that you will get 1-5 trades closing
per day. In an ideal world, you would be trading 10% of the account
for a 10% profit, thereby realizing 1% profit on each trade... in
other words for 1BTC account if you buy 0.1BTC of a coin and profit
10% then you profited 0.01 BTC or 1% of your account balance. But
unfortunately a 10% profit target takes longer to reach. 5% closes
fast. You could even trade 10% of the account with a 5% profit target,
but I suggest 5% of the account for a 5% profit target to be safe.

To summarize: as long as you have daily profits to withdraw, you are
in good shape, because SurgeTrader will take your principle and open
another surge trade for you, so you have more profits to collect down
the road.


# TODO

- re-issue limit orders that are older than 28 days (Bittrex changed max limit trade age to 28 days).
- do not trade coins newly added to Bittrex. Newly added coins get you into [the soup I got into with Decentraland](https://www.reddit.com/r/surgetraderbot/comments/7cef5j/dailyprofit_056/).
- automatic withdrawal of profits at 1am
- call takeprofits immediately after buy https://www.reddit.com/r/CryptoMarkets/comments/7a20lc/im_the_author_the_foss_crypto_trading_bot/dpbuwzw/
- throw exception if IsOpen == False but QuantityRemaining > 0
- email admin if exception thrown in program
- tasks.py profitreport must accept an email flag
- make the bot run on multiple exchanges: use Bitex and dependency injection instead of my homegrown python-bittrex to interact with Bittrex.


## Explain the declining estimated value

- simple pictures of emotional market cycle
- example of a trade that took 2-3 week to close
- bitcoin lost from 2013 to 2016
- emotional market cycle video

# DISCLAIMER

The author of this software is in no way responsible for any type of loss incurred
by those who chose to download and use it.
