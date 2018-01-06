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
from bittrex.bittrex import SELL_ORDERBOOK
from retry import retry
from supycache import supycache

# local
from .db import db
from . import mybittrex


LOGGER = logging.getLogger(__name__)
"""TODO: move print statements to logging"""

IGNORE_BY_IN = list()
"""TODO: move this list of coins to the system.ini file so users can customize"""
IGNORE_BY_IN.append('BURST') # https://steemit.com/cryptocurrency/@iceburst/the-death-of-burst-coin
IGNORE_BY_IN.append('UNO')   # in the processs of being delisted?
IGNORE_BY_IN.append('START')
IGNORE_BY_IN.append('UNB')


IGNORE_BY_FIND = 'ETH- USDT-'.split()
"""We do not trade the markets based on ETH or USDT."""
MAX_ORDERS_PER_MARKET = 3
"""The maximum number of purchases of a coin we will have open sell orders for
is 3. Sometimes a coin will surge on the hour, but drop on the day or week.
And then surge again on the hour, while dropping on the longer time charts.
We do not want to suicide our account by continually chasing a coin with this
chart pattern. MANA did this for a long time before recovering. But we dont
need that much risk."""
MIN_PRICE = 0.00000125
"""The coin must cost 100 sats or more because any percentage markup for a
cheaper coin will not lead to a change in price."""
MIN_VOLUME = 12
"Must have at least 12 BTC in transactions over last 24 hours"
MIN_GAIN = 5
"1-hour gain must be 5% or more"


@retry(exceptions=json.decoder.JSONDecodeError, tries=600, delay=5)
def number_of_open_orders_in(exchange, market):
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
    open_orders_list = exchange.get_open_orders(market)['result']
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
    print("\tAvailable btc={0}".format(avail))
    return avail


def record_buy(config_file, order_id, mkt, rate, amount):
    db.buy.insert(
        config_file=config_file,
        order_id=order_id, market=mkt, purchase_price=rate, amount=amount)
    db.commit()


def rate_for(exchange, mkt, btc):
    "Return the rate that works for a particular amount of BTC."

    coin_amount = 0
    btc_spent = 0
    orders = exchange.get_orderbook(mkt, SELL_ORDERBOOK)
    for order in orders['result']:
        btc_spent += order['Rate'] * order['Quantity']
        if btc_spent > 1.2* btc:
            coin_amount = btc / order['Rate']
            return order['Rate'], coin_amount

def config_top(config):
    _ = config.get('trade', 'top')
    return int(_)


def config_preserve(config):
    _ = config.get('trade', 'preserve')
    return float(_)


def config_min_volume(config):
    _ = config.get('trade', 'volume_min')
    return float(_)


def percent2ratio(percentage):
    return percentage / 100.0


def config_trade_size(config):
    holdings = float(config.get('trade', 'deposit'))
    trade_ratio = percent2ratio(float(config.get('trade', 'trade')))

    return holdings * trade_ratio


def config_trade_fallback(config):
    _ = config.get('trade', 'fallback')
    return float(_) / 100.0


def get_trade_size(config, btc):

    # Do not trade if we are configured to accumulate btc
    # (presumably for withdrawing a percentage for profits)
    if btc <= config_preserve(config):
        print("BTC balance <= amount to preserve")
        return 0

    # If we have more BTC than the size of each trade, then
    # make a trade of that size
    trade_size = config_trade_size(config)
    print("\tTrade size   ={}".format(trade_size))
    if btc >= trade_size:
        return trade_size

    # Otherwise do not trade
    return 0


def profitable_rate(entry, gain):

    x_percent = gain / 100.0
    take_profit = entry * x_percent + entry

    print(("On an entry of {0:.8f}, TP={1:.8f} for a {2} percent gain".format(
        entry, take_profit, gain)))

    return take_profit


def _buycoin(config_file, config, exchange, mkt, btc):
    "Buy into market using BTC. Current allocately 2% of BTC to each trade."

    size = get_trade_size(config, btc)

    if not size:
        print("No trade size. Returning.")
        return

    print("I will trade {0} BTC.".format(size))

    rate, amount_of_coin = rate_for(exchange, mkt, size)

    print("I get {0} units of {1} at the rate of {2:.8f} BTC per coin.".format(
        amount_of_coin, mkt, rate))

    result = exchange.buy_limit(mkt, amount_of_coin, rate)
    if result['success']:
        print("\tBuy was a success = {}".format(result))
        record_buy(config_file, result['result']['uuid'], mkt, rate, amount_of_coin)
    else:
        print("\tBuy FAILED: {}".format(result))


def buycoin(config_file, config, exchange, top_coins):
    "Buy top N cryptocurrencies."

    avail = available_btc(exchange)

    for market in top_coins:
        _buycoin(config_file, config, exchange, market[0], avail)


@supycache(cache_key='result')
def analyze_gain(exchange):

    def should_skip(name):
        for ignorable in IGNORE_BY_IN:
            if ignorable in name:
                print("\tIgnoring {} because {} is in({}).".format(
                    name, ignorable, IGNORE_BY_IN))
                return True

        for ignore_string in IGNORE_BY_FIND:
            if name.find(ignore_string) > -1:
                print('\tIgnore by find: ' + name)
                return True

        return False

    def get_recent_market_data():
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

    print("Number of markets = {0}".format(len(list(recent.keys()))))

    gain = list()

    for name, row in recent.items():

        print("Analysing {}...".format(name))

        if len(row) != 2:
            print("\t2 entries for market required. Perhaps this is the first run?")
            continue

        if should_skip(name):
            continue

        try:
            if markets[name]['BaseVolume'] < MIN_VOLUME:
                print("\t{} 24hr vol < {}".format(markets[name], MIN_VOLUME))
                continue
        except KeyError:
            print("\tKeyError locating {}".format(name))
            continue

        if number_of_open_orders_in(exchange, name) >= MAX_ORDERS_PER_MARKET:
            print('\tToo many open orders: ' + name)
            continue

        if row[0].ask < MIN_PRICE:
            print('\t{} costs less than {}.'.format(name, MIN_PRICE))
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

    gain = sorted(gain, key=lambda r: r[1], reverse=True)
    return gain


def topcoins(exchange, number_of_coins):
    top = analyze_gain(exchange)

    # print 'TOP: {}.. now filtering'.format(top[:10])
    top = [t for t in top if t[1] >= MIN_GAIN]
    # print 'TOP filtered on MIN_GAIN : {}'.format(top)


    print("Top 5 coins filtered on %gain={} and volume={}:\n{}".format(
        MIN_GAIN,
        MIN_VOLUME,
        pprint.pformat(top[:5], indent=4)))

    return top[:number_of_coins]


def process(config_file):
    from users import users
    config = users.read(config_file)

    exchange = mybittrex.make_bittrex(config)

    amount_to_buy = config_top(config)
    top_coins = topcoins(exchange, amount_to_buy)

    print("Buying coins for: {}".format(config_file))
    buycoin(config_file, config, exchange, top_coins)


def main(inis):

    for config_file in inis:
        process(config_file)

if __name__ == '__main__':
    argh.dispatch_command(main)
