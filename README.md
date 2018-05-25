# surgetrader
A python 3 library for general algorithmic trading and profit reporting.

## What working bots exist?

SurgeTrader has two working bots:

* HOURLY SURGE: The first one was designed to detect coins with the strongest gain in price over 1 hour. It would then buy them and set profit targets. You can read about it in [README-hourly.md](README-hourly.md)  ... I'm no longer running it.
* TELEGRAM CLIENT: The newer bot, scans Telegram channels for buy signals and automatically executes them. Then it sets profit targets. You can read about it in [README-telegram.md](README-telegram.md) ... I'm currently running it.

Both bot versions provide daily and monthly profit reports.

**Neither** implements any form of stop loss.

# DISCLAIMER

The author of this software is in no way responsible for any type of loss incurred
by those who chose to download and use it.

# LICENSE

GNU GPL.

# Other free bots

* [Krypto trading bot](https://github.com/ctubio/Krypto-trading-bot)
* [Zenbot](https://jaynagpaul.com/algorithmic-crypto-trading) - Carlos is releasing Code18 soon.
* [Gekko (freaking amazing)](https://gekko.wizb.it/)
