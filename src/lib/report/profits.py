#!/usr/bin/env python


import configparser
import argh
import collections
import logging
from retry import retry
from db import db
import mybittrex
from bittrex.bittrex import SELL_ORDERBOOK
from pprint import pprint

def loop_forever():
    while True:
        pass


logger = logging.getLogger(__name__)

def open_order(result):

    pprint(result['IsOpen'])
    return result['IsOpen']


def report_profit(config_file, b):
    import csv
    csv_file = config_file + ".csv"
    csvfile = open(csv_file, 'w', newline='')
    fieldnames = 'sell_closed sell_opened market units_sold sell_price sell_commission units_bought buy_price buy_commission profit'.split()
    csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    csv_writer.writeheader()

    for buy in db().select(
        db.buy.ALL,
        orderby=~db.buy.timestamp
    ):


        if buy.config_file != config_file:
            #print("config file != {}... skipping".format(config_file))
            continue

        if len(buy.sell_id) < 12:
            #print("No sell id ... skipping")
            continue

        so = b.get_order(buy.sell_id)['result']

        if open_order(so):
            print("Open order ... skipping")
            continue

        pprint(buy)
        pprint(so)

        sell_proceeds = so['Price'] - so['CommissionPaid']

        bo = b.get_order(buy.order_id)['result']

        buy_proceeds = bo['Price'] + bo['CommissionPaid']

        pprint("sell_proceeds = {}. buy Order = {}. buy proceeds = {}".format(
            sell_proceeds, bo, buy_proceeds))

        profit = sell_proceeds - buy_proceeds

        calculations = {
            'sell_closed': so['Closed'],
            'sell_opened': so['Opened'],
            'market': so['Exchange'],
            'units_sold': so['Quantity'],
            'sell_price': so['PricePerUnit'],
            'sell_commission': so['CommissionPaid'],
            'units_bought': bo['Quantity'],
            'buy_price': bo['PricePerUnit'],
            'buy_commission': bo['CommissionPaid'],
            'profit': profit
        }

        csv_writer.writerow(calculations)


def main(ini):

    config_file = ini
    config = configparser.RawConfigParser()
    config.read(config_file)

    b = mybittrex.make_bittrex(config)
    report_profit(config_file, b)

if __name__ == '__main__':
    argh.dispatch_command(main)
