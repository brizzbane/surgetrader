#!/usr/bin/env python

# core
import collections
import logging
import pprint
import ConfigParser

# 3rd party
import argh
from supycache import supycache

from retry import retry

# local
from db import db
import mybittrex
from bittrex.bittrex import SELL_ORDERBOOK


logger = logging.getLogger(__name__)


ignore_by_in = 'BURST START'.split()
ignore_by_find = 'ETH- USDT-'.split()
max_orders_per_market = 1
MIN_PRICE = 0.00000100

MIN_GAIN = 0.05 # need a 5 percent gain or it's not a surge!


def percent_gain(new, old):
    increase = (new - old)
    if increase:
        percent_gain = increase / old
    else:
        percent_gain = 0
    return percent_gain


def number_of_open_orders_in(b, market):
    orders = list()
    oo = b.get_open_orders(market)['result']
    if oo:
        # pprint.pprint(oo)
        for order in oo:
            if order['Exchange'] == market:
                orders.append(order)
        return len(orders)
    else:
        return 0

def record_gain(gain):
    # pprint.pprint(gain)

    for i, _gain in enumerate(gain, start=1):
        print "{0}: {1}".format(i, pprint.pformat(_gain))
        db.picks.insert(
            market=_gain[0],
            old_price=_gain[2],
            new_price=_gain[3],
            gain=_gain[1]
        )
        if i > 10:
            break

    db.commit()



@supycache(cache_key='result')
def analyze_gain(b, min_volume):

    recent = collections.defaultdict(list)

    markets = b.get_market_summaries(by_market=True)

    # pprint.pprint(markets)

    # take the 2 most recent pricings for each market and store in the
    # list 'recent'

    # having_query = db.market.
    for row in db().select(
        db.market.ALL,
        groupby=db.market.name
    ):
        for market_row in db(db.market.name == row.name).select(
                db.market.ALL,
                orderby=~db.market.timestamp,
                limitby=(0, 2)
        ):
            recent[market_row.name].append(market_row)

    print "Number of markets = {0}".format(len(recent.keys()))
    # pprint.pprint(recent)

    gain = list()

    for name, row in recent.iteritems():

        print name

        try:
            if min_volume and markets[name]['BaseVolume'] < min_volume:
                print "Ignoring on low volume {0}".format(markets[name])
                continue
        except KeyError:
            print "KeyError locating " + name
            continue

        leave = False

        for ignorable in ignore_by_in:
            if ignorable in name:
                print "\tIgnoring {} because {} is in({}).".format(
                    name, ignorable, ignore_by_in)
                leave = True
                break

        for f in ignore_by_find:
            if name.find(f) > -1:
                print '\tIgnore by find: ' + name
                leave = True

        if leave:
            continue

        if number_of_open_orders_in(b, name) >= max_orders_per_market:
            print 'Max open orders: ' + name
            continue

        if row[0].ask < MIN_PRICE:
            print 'Coin costs less than {}: {}'.format(MIN_PRICE, name)
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

    # record_gain(gain)

    gain = sorted(gain, key=lambda r: r[1], reverse=True)
    return gain


def report_btc_balance(b):
    bal = b.get_balance('BTC')
    pprint.pprint(bal)
    return bal['result']


def available_btc(b):
    bal = report_btc_balance(b)
    avail = bal['Available']
    print "Available btc={0}".format(avail)
    return avail


def record_buy(config_file, order_id, mkt, rate, amount):
    db.buy.insert(
        config_file=config_file,
        order_id=order_id, market=mkt, purchase_price=rate, amount=amount)
    db.commit()

def rate_for(b, mkt, btc):
    "Return the rate that works for a particular amount of BTC."

    coin_amount = 0
    btc_spent = 0
    orders = b.get_orderbook(mkt, SELL_ORDERBOOK)
    for order in orders['result']:
        btc_spent += order['Rate'] * order['Quantity']
        if btc_spent > 1.2* btc:
            break

    coin_amount = btc / order['Rate']
    return order['Rate'], coin_amount

def config_top(c):
    p = c.get('trade', 'top')
    return int(p)

def config_accumulate(c):
    p = c.get('trade', 'accumulate')
    return float(p)

def config_min_volume(c):
    p = c.get('trade', 'volume_min')
    return float(p)

def config_trade_size(c):
    p = c.get('trade', 'size')
    return float(p)

def config_trade_fallback(c):
    p = c.get('trade', 'fallback')
    return float(p) / 100.0

def get_trade_size(c, btc):
    s = config_trade_size(c)

    print "Getting trade size..."

    # Do not trade if we are configured to accumulate btc
    # (presumably for withdrawing a percentage for profits)
    if btc <= config_accumulate(c):
        return 0

    # If we have more BTC than the size of each trade, then
    # make a trade of that size
    if btc >= config_trade_size(c):
        return config_trade_size(c)

    # Otherwise do not trade
    return 0

def profitable_rate(entry, gain):

    x_percent = gain / 100.0
    tp = entry * x_percent + entry

    print("On an entry of {0:.8f}, TP={1:.8f} for a {2} percent gain".format(
        entry, tp, gain))

    return tp

def _buycoin(config_file, c, b, mkt, btc):
    "Buy into market using BTC. Current allocately 2% of BTC to each trade."

    print "{} has {} BTC available.".format(config_file, btc)

    size = get_trade_size(c, btc)

    if not size:
        print "No trade size. Returning."
        return

    print "I will trade {0} BTC.".format(size)

    rate, amount_of_coin = rate_for(b, mkt, size)

    print "I get {0} units of {1} at the rate of {2:.8f} BTC per coin.".format(
        amount_of_coin, mkt, rate)

    r = b.buy_limit(mkt, amount_of_coin, rate)
    if r['success']:
        print "Buy was a success = {}".format(r)
        record_buy(config_file, r['result']['uuid'], mkt, rate, amount_of_coin)

def buycoin(config_file, config, exchange, top_coins, min_volume=0):
    "Buy top N cryptocurrencies."


    avail = available_btc(exchange)

    for market in top_coins:

        _buycoin(config_file, config, exchange, market[0], avail)

def topcoins(exchange, min_volume, n):
    top = analyze_gain(exchange, min_volume)


    # print 'TOP: {}.. now filtering'.format(top)
    top = [t for t in top if t[1] > MIN_GAIN]
    print 'TOP filtered on MIN_GAIN : {}'.format(top)

    return top[:n]

def process(config_file):
    config = ConfigParser.RawConfigParser()
    config.read(config_file)

    exchange = mybittrex.make_bittrex(config)

    min_volume = config_min_volume(config)

    amount_to_buy = config_top(config)
    top_coins = topcoins(exchange, min_volume, amount_to_buy)

    print "Buying coins for: {}".format(config_file)
    buycoin(config_file, config, exchange, top_coins, min_volume)

def main(inis):

    for config_file in inis.split():
        process(config_file)

if __name__ == '__main__':
    argh.dispatch_command(main)
