# surgetrader
A python **3** bot designed to profit on price surges detected at BitTrex.

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
1. `pip3 install -r requirements.txt`
1. If `pip3` is not available, then you may try calling `pip` instead. But make sure that `pip` is indeed a Python **3** `pip`
and not a Python 2 one by typing `which pip` and looking at the path of the executable.

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
    @daily       cd ~/prg/surgetrader/src/ ; $INVOKE cancelsells
    11   0 * * * cd ~/prg/surgetrader/src/ ; $INVOKE profitreport -d yesterday
    22   0 1 * * cd ~/prg/surgetrader/src/ ; $INVOKE profitreport -d lastmonth

### Note

What is `cancelsells`? It is a hack I put in place because Bittrex
recently decided to close all trades older than 28 days. So what
`cancelsells` does is cancel sell orders once a week and delete the
`sell_id` from the database. Then the takeprofit task will notice
that a buy trade does not have a sell limit order in place and will
automatically place a new one.

This code has not been thoroughly tested.

Some people want to set profit targets as soon as they buy instead of doing it every 5 minutes.
You can see the modifications that one individual made
[here](https://www.reddit.com/r/CryptoMarkets/comments/7a20lc/im_the_author_the_foss_crypto_trading_bot/dpbuwzw/).


### Test it Out!

Do **NOT** test this out by typing `invoke download`. If you do, you run the risk of prematurely buying a coin - not a big deal.
But it's better to test it by typing `invoke takeprofit`

## System Hygiene

Occasionally, the daily profit report will email you, informing you that the system crashed. The two common reasons for crashing are:
1. Bittrex is performing temporary maintenance on a coin
2. Bittrex is delisting a market
3. An order closed but did not sell. This can happen if you clicked the "X" button on a open sell order so the order closed but did not sell.

You need to go to Bittrex and see why the bot crashed ... or connect with me in [Discord](https://discord.me/cashmoney). If the coin
is under maintenance, you will see something like [this](http://take.ms/WtFsc) when you visit the market.

### Market Under Maintenance

You may get errors when the profit report runs if a market is under maintenance. For example on January 7, 2018 the market `BTC-SHIFT` was
undergoing automated maintence [as this screenshot shows](http://take.ms/Dz9Rb). So, when I rain the daily profit report, I got [this execution
log and error](https://gist.github.com/metaperl/5bc3e5bbebf9aa9c88073511b887b6cb). If this is the case, then when you invoke the profit report,
tell it to skip certain markets (or wait until maintenance is through). Here is how to skip `BTC-SHIFT` in the profit report:

    cd ~/prg/surgetrader/src/ ; invoke profitreport -d yesterday -s SHIFT

You can put as many markets there as you like:

    cd ~/prg/surgetrader/src/ ; invoke profitreport -d yesterday -s "SHIFT CRW NBT OK"


### Market Delisted

Occasionally you will get an email from SurgeTraderBot with the subject "SurgeTraderBOT aborted execution on exception"
and in the body of the email you will see something like this:

    Traceback (most recent call last):
      File "/home/schemelab/prg/surgetrader/src/lib/report/profit.py", line 263, in main
        html, total_profit = report_profit(config_file, exchange, _date)
      File "/home/schemelab/prg/surgetrader/src/lib/report/profit.py", line 150, in report_profit
        raise Exception("Order closed but did not sell: {}".format(so))
    Exception: Order closed but did not sell: {'AccountId': None, 'OrderUuid': '0a5ef35c-edde-49fe-b569-8a4c7e2f7259', 'Exchange': 'BTC-XAUR',

The reason this happens is that BitTrex delists coins or the coin is undergoing maintenance at the moment.
So what happened is that you bought a coin and before
you could sell it, Bittrex delisted it or is doing some routine wallet maintenace.

If the market is delisted, you must delete those records from the database so the error does not occur again. if the market is just under
maintenance, then you can wait until it returns.

Let's continue our discussion about deleting trades from the database in the case of a market being delisted. In this
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

### "Order Closed But Did Not Sell"

For whatever reason, a (sell) order that you put up may be closed --- either manually by you or by Bittrex for some odd reason. In this case, you also need to remove the order
from the database so that the profit report can complete successfully. Here is a transcript of this happening to me and me solving it:

    Traceback (most recent call last):
      File "/home/schemelab/prg/surgetrader/src/lib/report/profit.py", line 327, in main
        html, total_profit = report_profit(config_file, exchange, _date, skip_markets)
      File "/home/schemelab/prg/surgetrader/src/lib/report/profit.py", line 211, in report_profit
        raise Exception("Order closed but did not sell: {}".format(so))
    Exception: Order closed but did not sell: {'AccountId': None, 'OrderUuid': 'b44f845b-1485-4d6a-a807-bf4278772648', 'Exchange': 'BTC-1ST', 'Type': 'LIMIT_SELL', 'Quantity': 353.35689044, 'QuantityRemaining': 353.35689044, 'Limit': 2.971e-05, 'Reserved': 353.35689044, 'ReserveRemaining': 353.35689044, 'CommissionReserved': 0.0, 'CommissionReserveRemaining': 0.0, 'CommissionPaid': 0.0, 'Price': 0.0, 'PricePerUnit': None, 'Opened': '2017-12-10T03:05:12.393', 'Closed': '2017-12-13T16:22:53.243', 'IsOpen': False, 'Sentinel': '1b92cdee-7f35-40e0-aa0f-85b678b45858', 'CancelInitiated': False, 'ImmediateOrCancel': False, 'IsConditional': False, 'Condition': 'NONE', 'ConditionTarget': None}

    sqlite> SELECT * FROM buy WHERE sell_id='b44f845b-1485-4d6a-a807-bf4278772648';
    2132|26c5f0b9-a17f-4211-9933-3f52a0d8e586|BTC-1ST|2.83e-05|2.9715e-05|353.356890459364|2017-12-09 22:03:25|ini-steadyvest@protonmail.ini|b44f845b-1485-4d6a-a807-bf4278772648
    sqlite> DELETE FROM buy WHERE sell_id='b44f845b-1485-4d6a-a807-bf4278772648';


## Manual Usage

All usage of SurgeTrader, whether automated or manual, occurs with your current working directory set to `src`:

    shell> cd $HOME/gitclones/surgetrader/src

All usage of SurgeTrader is controlled by calling `invoke`. A very simple thing that should work is:

    shell> invoke download

# DEVELOPER DOCS

Developers please read the code documentation. The best place to start is
[src/tasks.py](https://gitlab.com/metaperl/surgetrader/blob/master/src/tasks.py)
because all functionality of this application can be accessed that way.

You may also join [the developer Discord channel](https://discord.gg/uYHEsh5).

# User-Level Docs (show me the money)

The first thing you need to understand is that SurgeTrader detects
surges in coins. The thing about a surging coin is that you may be
late to the party: you might be buying just as the sell-off is about
to start, which means you might not collect your profit immediately.

Sure, there are those times, where the same coin gives you 3 or 4
profits in 3 or 4 hours:
![](https://api.monosnap.com/rpc/file/download?id=8RKinNxVaGOlJCRMCgIbQY2oZlxKQT)

But sometimes you get caught out at the top of [a teacup and handle
formation](http://www.investopedia.com/terms/c/cupandhandle.asp) and it might be 3-4 weeks before a trade closes. [Patience](https://www.reddit.com/r/surgetraderbot/search?q=%23patience&restrict_sr=on)
my dear friend, [Patience](https://www.reddit.com/r/surgetraderbot/search?q=%23patience&restrict_sr=on).

## Media and Contact

Direct chat with the bot developer is via [his Discord](https://discord.gg/5WPHMwu).
Forum chat is available on [the official Reddit forum](https://www.reddit.com/r/surgetraderbot/). Subscribe to get critical updates/news.
Various orientation posts on SurgeTraderBot:
* [I'm the author the FOSS crypto trading bot SurgeTrader #AMA](https://www.reddit.com/r/CryptoMarkets/comments/7a20lc/im_the_author_the_foss_crypto_trading_bot/).
*


# TODO

- re-issue limit orders that are older than 28 days (Bittrex changed max limit trade age to 28 days).
- do not trade coins newly added to Bittrex. Newly added coins get you into [the soup I got into with Decentraland](https://www.reddit.com/r/surgetraderbot/comments/7cef5j/dailyprofit_056/).
- automatic withdrawal of profits at 1am
- call takeprofits immediately after buy https://www.reddit.com/r/CryptoMarkets/comments/7a20lc/im_the_author_the_foss_crypto_trading_bot/dpbuwzw/
- throw exception if IsOpen == False but QuantityRemaining > 0
- email admin if exception thrown in program
- tasks.py profitreport must accept an email flag
- make the bot run on multiple exchanges: use Bitex and dependency injection instead of my homegrown python-bittrex to interact with Bittrex.
- log program information via logging instead of print statements and save them to disk as well as printing them.
- use unique names for profit reports written to HTML/CSV


# DISCLAIMER

The author of this software is in no way responsible for any type of loss incurred
by those who chose to download and use it.
