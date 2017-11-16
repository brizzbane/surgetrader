#!/usr/bin/env python

# Core
from datetime import datetime
import logging
import pprint


# 3rd Party
import argh
from retry import retry

# Local
from .db import db
from . import mybittrex


logger = logging.getLogger(__name__)

import json
@retry(exceptions=json.decoder.JSONDecodeError, tries=600, delay=5)
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
