#!/usr/bin/env python



# core
import logging
import pprint

# pypi

# local
from . import mybittrex
from .db import db



logging.basicConfig(
    format='%(lineno)s %(message)s',
    level=logging.WARN
)

ONE_PERCENT = 1.0 / 100.0
TWO_PERCENT = 2.0 / 100.0


LOGGER = logging.getLogger(__name__)



def single_and_double_satoshi_scalp(price):
    # forget it - huge sell walls in these low-satoshi coins!
    return price + 2e-8


def __takeprofit(entry, gain):

    x_percent = gain / 100.0
    profit_target = entry * x_percent + entry

    print(("On an entry of {0:.8f}, TP={1:.8f} for a {2} percent gain".format(
        entry, profit_target, gain)))

    return profit_target

def _takeprofit(exchange, percent, row):

    profit_target = __takeprofit(entry=row.purchase_price, gain=percent)

    #amount_to_sell = order['Quantity'] - 1e-8
    #amount_to_sell = order['Quantity']
    amount_to_sell = row['amount']

    print("b.sell_limit({}, {}, {})".format(row.market, amount_to_sell, profit_target))
    result = exchange.sell_limit(row.market, amount_to_sell, profit_target)
    pprint.pprint(result)

    if result['success']:
        row.update_record(selling_price=profit_target, sell_id=result['result']['uuid'])
        db.commit()


#@retry()
def takeprofit(config_file, exchange, percent):

    rows = db((db.buy.selling_price == None) & (db.buy.config_file == config_file)).select()
    for row in rows:
        print("\t", row)

        # if row['config_file'] != config_file:
        #     print "my config file is {} but this one is {}. skipping".format(
        #         config_file, row['config_file'])
        #     continue

        order = exchange.get_order(row['order_id'])
        print("unsold row {}".format(pprint.pformat(order)))
        order = order['result']
        if not order['IsOpen']:
            _takeprofit(exchange, percent, row)
        else:
            print("""Buy has not been filled. Cannot sell for profit until it does.
                  You may want to manually cancel this buy order.""")


def _clearprofit(exchange, row):

    print("Clearing Profit for {}".format(row))

    result = exchange.cancel(row['sell_id'])

    if result['success']:
        print("\t\tSuccess: {}".format(result))
        row.update_record(selling_price=None, sell_id=None)
        db.commit()
    else:
        raise Exception("Order cancel failed: {}".format(result))

def clearorder(exchange, sell_id):
    row = db((db.buy.sell_id == sell_id)).select().first()
    if not row:
        raise Exception("Could not find row with sell_id {}".format(sell_id))

    _clearprofit(exchange, row)

def clear_order_id(exchange, sell_order_id):
    "Used in conjunction with `invoke clearorderid`"
    clearorder(exchange, sell_order_id)


def clearprofit(exchange):
    "Used in conjunction with `invoke cancelsells`"
    openorders = exchange.get_open_orders()['result']
    count = 0
    for openorder in openorders:
        if openorder['OrderType'] == 'LIMIT_SELL':
            count += 1
            print("{}: {} --->{}".format(count, openorder, openorder['OrderUuid']))
            clearorder(exchange, openorder['OrderUuid'])

#    rows = db((db.buy.sell_id != None) & (db.buy.config_file == config_file)).select()
#    for i, row in enumerate(rows):
#        print("  -- Row {}".format(i))
#        clearorder(exchange, row)


def prep(config_file):
    from users import users

    config = users.read(config_file)
    exchange = mybittrex.make_bittrex(config)
    return config, exchange

def take_profit(config_file):

    config, exchange = prep(config_file)
    percent = float(config.get('trade', 'takeprofit'))

    print("Setting profit targets for {}".format(config_file))

    takeprofit(config_file, exchange, percent)

def clear_profit(config_file):
    _, exchange = prep(config_file)
    clearprofit(exchange)
