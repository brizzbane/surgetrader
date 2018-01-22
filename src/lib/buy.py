"""Perform purchases of coins based on technical analysis.

Example:

        shell> invoke buy

`src/tasks.py` has a buy task that will call main of this module.

Todo:
    * This module is perfect. Are you kidding me?

"""

# core
import collections
import json
import logging
import pprint

# 3rd party
import argh
from retry import retry
from supycache import supycache
from bittrex.bittrex import SELL_ORDERBOOK

# local
import lib.config
import lib.logconfig
from .db import db
from . import mybittrex

#LOGGER = logging.getLogger(__name__)
LOG = lib.logconfig.app_log
"""TODO: move LOG.debug statements to logging"""


SYS_INI = lib.config.System()

IGNORE_BY_IN = SYS_INI.ignore_markets_by_in
"Coins we wish to avoid"

IGNORE_BY_FIND = SYS_INI.ignore_markets_by_find
"We do not trade ETH or USDT based markets"


MAX_ORDERS_PER_MARKET = SYS_INI.max_open_trades_per_market
"""The maximum number of purchases of a coin we will have open sell orders for
is 3. Sometimes a coin will surge on the hour, but drop on the day or week.
And then surge again on the hour, while dropping on the longer time charts.
We do not want to suicide our account by continually chasing a coin with this
chart pattern. MANA did this for a long time before recovering. But we dont
need that much risk."""

MIN_PRICE = SYS_INI.min_price
"""The coin must cost 100 sats or more because any percentage markup for a
cheaper coin will not lead to a change in price."""

MIN_VOLUME = SYS_INI.min_volume
"Must have at least a certain amount of BTC in transactions over last 24 hours"

MIN_GAIN = SYS_INI.min_gain
"1-hour gain must be 5% or more"


@retry(exceptions=json.decoder.JSONDecodeError, tries=600, delay=5)
def number_of_open_orders_in(openorders, market):
    """Maximum number of unclosed SELL LIMIT orders for a coin.

    SurgeTrader detects hourly surges. On occasion the hourly surge is part
    of a longer downtrend, leading SurgeTrader to buy on surges that do not
    close. We do not want to keep buying false surges so we limit ourselves to
    3 open orders on any one coin.

    Args:
        exchange (int): The exchange object.
        market (str): The coin.

    Returns:
        int: The number of open orders for a particular coin.

    """
    orders = list()
    open_orders_list = openorders['result']
    if open_orders_list:
        for order in open_orders_list:
            if order['Exchange'] == market:
                orders.append(order)

    return len(orders)


def percent_gain(new, old):
    """The percentage increase from old to new.

    Returns:
        float: percentage increase [0.0,100.0]
    """
    gain = (new - old) / old
    gain *= 100
    return gain


def obtain_btc_balance(exchange):
    """Get BTC balance.

    Returns:
        dict: The account's balance of BTC.
    """
    bal = exchange.get_balance('BTC')
    return bal['result']


def available_btc(exchange):
    """Get BTC balance.

    Returns:
        float: The account's balance of BTC.
    """
    bal = obtain_btc_balance(exchange)
    avail = bal['Available']
    LOG.debug("\tAvailable btc={0}".format(avail))
    return avail


def record_buy(config_file, order_id, mkt, rate, amount):
    """Store the details of a coin purchase.

    Create a new record in the `buy` table.

    Returns:
        Nothing
    """
    db.buy.insert(
        config_file=config_file,
        order_id=order_id, market=mkt, purchase_price=rate, amount=amount)
    db.commit()


def rate_for(exchange, mkt, btc):
    "Return the rate that allows you to spend a particular amount of BTC."

    coin_amount = 0
    btc_spent = 0
    orders = exchange.get_orderbook(mkt, SELL_ORDERBOOK)
    for order in orders['result']:
        btc_spent += order['Rate'] * order['Quantity']
        if btc_spent > 1.4* btc:
            coin_amount = btc / order['Rate']
            return order['Rate'], coin_amount
    return 0






def percent2ratio(percentage):
    """Convert a percentage to a float.

    Example:
        if percentage == 5, then return 5/100.0:

    """
    return percentage / 100.0


def calculate_trade_size(user_config):
    """How much BTC to allocate to a trade.

    Given the seed deposit and the percentage of the seed to allocate to each
    trade.

    Returns:
        float : the amount of BTC to spend on trade.
    """

    holdings = user_config.trade_deposit
    trade_ratio = percent2ratio(user_config.trade_trade)

    return holdings * trade_ratio


def get_trade_size(user_config, btc):
    "Determine how much BTC to spend on a buy."

    # Do not trade if we are configured to accumulate btc
    # (presumably for withdrawing a percentage for profits)
    if btc <= user_config.trade_preserve:
        LOG.debug("BTC balance <= amount to preserve")
        return 0

    # If we have more BTC than the size of each trade, then
    # make a trade of that size
    trade_size = calculate_trade_size(user_config)
    LOG.debug("\tTrade size   ={}".format(trade_size))
    if btc >= trade_size:
        return trade_size

    # Otherwise do not trade
    return 0


def fee_adjust(btc, exchange):
    """The amount of BTC that can be spent on coins sans fees.

    For instance if you want to spend 0.03BTC per trade, but the exchange charges 0.25% per trade,
    then you can spend 0.03 -  0.03 * 0.0025 instead of 0.03
    """

    exchange_fee = 0.25 # 0.25% on Bittrex
    LOG.debug("Adjusting {} trade size to respect {}% exchange fee on {}".format(
        btc, exchange_fee, exchange))

    exchange_fee /= 100.0

    adjusted_spend = btc - btc * exchange_fee
    return adjusted_spend



def _buycoin(config_file, user_config, exchange, mkt, btc):
    "Buy into market using BTC."

    size = get_trade_size(user_config, btc)

    if not size:
        LOG.debug("No trade size. Returning.")
        return
    else:
        size = fee_adjust(size, exchange)

    LOG.debug("I will trade {0} BTC.".format(size))

    rate, amount_of_coin = rate_for(exchange, mkt, size)

    LOG.debug("I get {0} units of {1} at the rate of {2:.8f} BTC per coin.".format(
        amount_of_coin, mkt, rate))

    result = exchange.buy_limit(mkt, amount_of_coin, rate)
    if result['success']:
        LOG.debug("\tBuy was a success = {}".format(result))
        record_buy(config_file, result['result']['uuid'], mkt, rate, amount_of_coin)
    else:
        LOG.debug("\tBuy FAILED: {}".format(result))


def buycoin(config_file, user_config, exchange, top_coins):
    "Buy top N cryptocurrencies."

    avail = available_btc(exchange)

    for market in top_coins:
        _buycoin(config_file, user_config, exchange, market[0], avail)


@supycache(cache_key='result')
def analyze_gain(exchange):
    """Find the increase in coin price.

    The market database table stores the current ask price of all coins.
    Every hour `invoke download` creates another row in this table. Then when
    `invoke buy` gets to the analyze_gain function, analyze_gain pulls the 2
    most recent rows from market and subtracts the ask prices to determine the
    1-hour price gain.

    Returns:
        list : A list of 5-tuples of this form
           (
                name,  # the market name, e.g. "BTC-NEO"
                percent_gain(row[0].ask, row[1].ask), # 1-hour price gain
                row[1].ask, # price this hour
                row[0].ask, # prince 1 hour ago
                'https://bittrex.com/Market/Index?MarketName={0}'.format(name),
            )
    """
    def should_skip(name):
        """Decide if a coin should be part of surge analysis.

        IGNORE_BY_IN filters out coins that I do not trust.
        IGNORE_BY_FIND filters out markets that are not BTC-based.
          E.g: ETH and USDT markets.
        """
        for ignorable in IGNORE_BY_IN:
            if ignorable in name:
                LOG.debug("\tIgnoring {} because {} is in({}).".format(
                    name, ignorable, IGNORE_BY_IN))
                return True

        for ignore_string in IGNORE_BY_FIND:
            if name.find(ignore_string) > -1:
                LOG.debug('\tIgnore by find: ' + name)
                return True

        return False

    def get_recent_market_data():
        """Get price data for the 2 time points.

        SurgeTrader detects changes in coin price. To do so, it subtracts the
        price of the coin at one point in time versus another point in time.
        This function gets the price data for 2 points in time so the difference
        can be calculated.
        """
        retval = collections.defaultdict(list)

        for row in db().select(db.market.ALL, groupby=db.market.name):
            for market_row in db(db.market.name == row.name).select(
                    db.market.ALL,
                    orderby=~db.market.timestamp,
                    limitby=(0, 2)
            ):
                retval[market_row.name].append(market_row)

        return retval

    markets = exchange.get_market_summaries(by_market=True)
    recent = get_recent_market_data()

    openorders = exchange.get_open_orders()

    LOG.debug("<ANALYZE_GAIN numberofmarkets={0}>".format(len(list(recent.keys()))))

    gain = list()

    for name, row in recent.items():

        LOG.debug("Analysing {}...".format(name))

        if len(row) != 2:
            LOG.debug("\t2 entries for market required. Perhaps this is the first run?")
            continue

        if should_skip(name):
            continue

        try:
            if markets[name]['BaseVolume'] < MIN_VOLUME:
                LOG.debug("\t{} 24hr vol < {}".format(markets[name], MIN_VOLUME))
                continue
        except KeyError:
            LOG.debug("\tKeyError locating {}".format(name))
            continue

        if number_of_open_orders_in(openorders, name) >= MAX_ORDERS_PER_MARKET:
            LOG.debug('\tToo many open orders: ' + name)
            continue

        if row[0].ask < MIN_PRICE:
            LOG.debug('\t{} costs less than {}.'.format(name, MIN_PRICE))
            continue

        gain.append(
            (
                name,
                percent_gain(row[0].ask, row[1].ask),
                row[1].ask,
                row[0].ask,
                'https://bittrex.com/Market/Index?MarketName={0}'.format(name),
            )
        )

    LOG.debug("</ANALYZE_GAIN>")

    gain = sorted(gain, key=lambda r: r[1], reverse=True)
    return gain


def topcoins(exchange, number_of_coins):
    """Find the coins with the greatest change in price.

    Calculate the gain of all BTC-based markets. A market is where
    one coin is exchanged for another, e.g: BTC-XRP.

    Markets must meet certain criteria:
        * 24-hr volume of MIN_VOLUME
        * price gain of MIN_GAIN
        * BTC-based market only
        * Not filtered out because of should_skip()
        * Cost is 125 satoshis or more

    Returns:
        list : the markets which are surging.
    """
    top = analyze_gain(exchange)

    # LOG.debug 'TOP: {}.. now filtering'.format(top[:10])
    top = [t for t in top if t[1] >= MIN_GAIN]
    # LOG.debug 'TOP filtered on MIN_GAIN : {}'.format(top)


    LOG.debug("Top 5 coins filtered on %gain={} and volume={}:\n{}".format(
        MIN_GAIN,
        MIN_VOLUME,
        pprint.pformat(top[:5], indent=4)))

    return top[:number_of_coins]


def process(config_file):
    """Buy coins for every configured user of the bot."""
    user_config = lib.config.User(config_file)

    exchange = mybittrex.make_bittrex(user_config.config)

    top_coins = topcoins(exchange, user_config.trade_top)

    LOG.debug("------------------------------------------------------------")
    LOG.debug("Buying coins for: {}".format(config_file))
    buycoin(config_file, user_config, exchange, top_coins)


def main(inis):
    """Buy coins for every configured user of the bot."""

    for config_file in inis:
        process(config_file)

if __name__ == '__main__':
    argh.dispatch_command(main)
