#!/usr/bin/env python



# core
import collections
import configparser
from datetime import datetime
import logging
import pprint

# pypi
import argh
from retry import retry
from bittrex.bittrex import SELL_ORDERBOOK

# local
from . import mybittrex
from .db import db



logging.basicConfig(
    format='%(lineno)s %(message)s',
    level=logging.WARN
)

one_percent = 1.0 / 100.0
two_percent = 2.0 / 100.0


logger = logging.getLogger(__name__)



def single_and_double_satoshi_scalp(price):
    # forget it - huge sell walls in these low-satoshi coins!
    return price + 2e-8


def __takeprofit(entry, gain):

    x_percent = gain / 100.0
    tp = entry * x_percent + entry

    print(("On an entry of {0:.8f}, TP={1:.8f} for a {2} percent gain".format(
        entry, tp, gain)))

    return tp

def _takeprofit(b, percent, row):

    tp = __takeprofit(entry=row.purchase_price, gain=percent)

    print("b.sell_limit({}, {}, {})".format(row.market, row.amount, tp))
    r = b.sell_limit(row.market, row.amount, tp)
    pprint.pprint(r)

    if r['success']:
        row.update_record(selling_price=tp, sell_id=r['result']['uuid'])
        db.commit()


#@retry()
def takeprofit(config_file, b, p):


    rows = db((db.buy.selling_price == None) & (db.buy.config_file == config_file)).select()
    for row in rows:
        print("\t", row)

        # if row['config_file'] != config_file:
        #     print "my config file is {} but this one is {}. skipping".format(
        #         config_file, row['config_file'])
        #     continue

        o = b.get_order(row['order_id'])
        print("unsold row {}".format(pprint.pformat(o)))
        o = o['result']
        if not o['IsOpen']:
            _takeprofit(b, p, row)



def main(ini, dry_run=False):

    config_file = ini

    from users import users

    config = users.read(config_file)

    b = mybittrex.make_bittrex(config)
    percent = float(config.get('trade', 'takeprofit'))

    print("Setting profit targets for {}".format(ini))

    takeprofit(config_file, b, percent)

if __name__ == '__main__':
    argh.dispatch_command(main)
