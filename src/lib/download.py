#!/usr/bin/env python


import argh
import logging
import pprint
from datetime import datetime
from retry import retry
from .db import db
from . import mybittrex
import configparser

logger = logging.getLogger(__name__)


#@retry(tries=10, delay=3)
def main(ini):

    config_file = ini
    from users import users

    config = users.read(config_file)

    b = mybittrex.make_bittrex(config)


    print("Getting market summaries")
    markets = b.get_market_summaries()

    with open("tmp/markets.json", "w") as markets_file:
        markets_file.write(pprint.pformat(markets['result']))

    print("Populating database")
    for market in markets['result']:

        db.market.insert(
            name=market['MarketName'],
            ask=market['Ask'],
            timestamp=datetime.now()
        )

    db.commit()

if __name__ == '__main__':
    argh.dispatch_command(main)
