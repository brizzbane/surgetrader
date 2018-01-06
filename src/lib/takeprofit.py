#!/usr/bin/env python



# core
import logging
import pprint

# pypi
import argh

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

def _takeprofit(exchange, percent, order, row):

    profit_target = __takeprofit(entry=row.purchase_price, gain=percent)

    #amount_to_sell = order['Quantity'] - 1e-8
    amount_to_sell = order['Quantity']

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
            _takeprofit(exchange, percent, order, row)


def _clearprofit(exchange, row, order):

    print("Clearing Profit for {} with order data = {}".format(row, order))

    result = exchange.cancel(row['order_id'])
    # pprint.pprint(result)

    if result['success']:
        print("\tSuccess: {}".format(result))
        row.update_record(selling_price=None, sell_id=None)
        db.commit()
    else:
        raise Exception("Order cancel failed: {}".format(result))

    # TODO: only update records on Success
    # Why am I updating in all cases. Because of feedback like this from the program:
    # Clearing Profit for {} with order data = {} <Row {'id': 1885, 'order_id': '07f42744-6a05-4686-9649-7fc50bdb209f', 'config_file': 'ini-steadyvest@protonmail.ini', 'market': 'BTC-BCY', 'purchase_price': 5.4e-05, 'selling_price': 5.508e-05, 'sell_id': 'b8f2e141-5e1b-4e16-a40d-a5363676c965', 'amount': 1666.6666666666667, 'timestamp': datetime.datetime(2017, 11, 5, 16, 0, 27)}> {'AccountId': None, 'OrderUuid': 'b8f2e141-5e1b-4e16-a40d-a5363676c965', 'Exchange': 'BTC-BCY', 'Type': 'LIMIT_SELL', 'Quantity': 1666.66666666, 'QuantityRemaining': 1666.66666666, 'Limit': 5.508e-05, 'Reserved': 1666.66666666, 'ReserveRemaining': 1666.66666666, 'CommissionReserved': 0.0, 'CommissionReserveRemaining': 0.0, 'CommissionPaid': 0.0, 'Price': 0.0, 'PricePerUnit': None, 'Opened': '2017-11-05T21:05:02.7', 'Closed': None, 'IsOpen': True, 'Sentinel': 'fc4f3b40-5d92-4376-8a27-d82d16df573f', 'CancelInitiated': False, 'ImmediateOrCancel': False, 'IsConditional': False, 'Condition': 'NONE', 'ConditionTarget': None}
    #  Failed: {'success': False, 'message': 'ORDER_NOT_OPEN', 'result': None}
    # You read that right: the exchange returned True for IsOpen yet when I tell the exchange to cancel the order it says ORDER_NOT_OPEN




def clearprofit(config_file, exchange):

    rows = db((db.buy.sell_id != None) & (db.buy.config_file == config_file)).select()
    for row in rows:

        order = exchange.get_order(row['sell_id'])
        order = order['result']
        if order['IsOpen']:
            _clearprofit(exchange, row, order)

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
    config, exchange= prep(config_file)
    clearprofit(config_file, exchange)

if __name__ == '__main__':
    argh.dispatch_command(main)
