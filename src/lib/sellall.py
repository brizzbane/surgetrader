#!/usr/bin/env python

# core
import configparser
import collections
import logging
import pprint
from pprint import pprint

# 3rd party
import argh
from retry import retry

# local
import lib.logconfig
from . import mybittrex
from bittrex.bittrex import SELL_ORDERBOOK
from .db import db


LOG = lib.logconfig.app_log


def loop_forever():
    while True:
        pass


logger = logging.getLogger(__name__)


def cancelall(b):
    orders = b.get_open_orders()

    for order in orders['result']:
        LOG.debug(order)
        sell_id = order['OrderUuid']
        r = b.cancel(sell_id)
        LOG.debug(r)
        db(db.buy.sell_id == sell_id).delete()
        db.commit()



def sellall(b):
    cancelall(b)
    balances = b.get_balances()
    for balance in balances['result']:
        LOG.debug("-------------------- {}".format(balance['Currency']))
        LOG.debug(balance)

        if not balance['Available'] or balance['Currency'] == 'BTC':
            LOG.debug("\tno balance or this is BTC")
            continue

        skipcoin = "CRYPT TIT GHC UNO DAR ARDR DGD MTL SNGLS SWIFT TIME TKN XAUR"
        if balance['Currency'] in skipcoin:
            LOG.debug("\tthis is a skipcoin")
            continue

        market = "BTC-" + balance['Currency']

        LOG.debug(balance)

        ticker = b.get_ticker(market)['result']
        LOG.debug(ticker)

        my_ask = ticker['Bid'] - 1e-8

        LOG.debug(("My Ask = {}".format(my_ask)))

        r = b.sell_limit(market, balance['Balance'], my_ask)
        LOG.debug(r)


def main(ini):

    config_file = ini
    config = configparser.RawConfigParser()
    config.read(config_file)

    b = mybittrex.make_bittrex(config)
    sellall(b)

if __name__ == '__main__':
    argh.dispatch_command(main)
