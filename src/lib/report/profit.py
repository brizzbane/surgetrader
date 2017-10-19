#!/usr/bin/env python


# core
import configparser
import argh
import collections
import logging
from pprint import pprint

# 3rd party
import meld3
from retry import retry

# local
from ..db import db
from .. import mybittrex
from bittrex.bittrex import SELL_ORDERBOOK
from users import users


logger = logging.getLogger(__name__)

def open_order(result):

    pprint(result['IsOpen'])
    return result['IsOpen']

def close_date(time_string):
    from datetime import datetime
    datetime_format = '%Y-%m-%dT%H:%M:%S'

    (time_string, _) = time_string.split('.')
    dt = datetime.strptime(time_string, datetime_format)
    return dt.date()

def report_profit(config_file, b, on_date=None):
    config = users.read(config_file)

    html_template = open('lib/report/profit.html', 'r').read()
    html_template = meld3.parse_htmlstring(html_template)
    html_outfile = open("tmp/" + config_file + ".html", 'wb')

    import csv
    csv_file = "tmp/" + config_file + ".csv"
    csvfile = open(csv_file, 'w', newline='')
    fieldnames = 'sell_closed sell_opened market units_sold sell_price sell_commission units_bought buy_price buy_commission profit'.split()
    csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    csv_writer.writeheader()

    closed_orders = list()

    for buy in db().select(
        db.buy.ALL,
        orderby=~db.buy.timestamp
    ):
        if buy.config_file != config_file:
            #print("config file != {}... skipping".format(config_file))
            continue

        if (not buy.sell_id) or (len(buy.sell_id) < 12):
            #print("No sell id ... skipping")
            continue

        so = b.get_order(buy.sell_id)['result']

        if open_order(so):
            print("Open order ... skipping")
            # TODO: fill in open orders part of template
            continue

        if on_date:
            _close_date = close_date(so['Closed'])
            if _close_date != on_date:
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
        closed_orders.append(calculations)


    html_template.findmeld('acctno').content(config_file)
    html_template.findmeld('name').content(config.get('client', 'name'))
    html_template.findmeld('date').content("Transaction Log for Previous Day")

    def satoshify(f):
        return '{:.8f}'.format(f)

    def render_row(element, data, append=None):
        for field_name, field_value in data.items():
            if field_name == 'units_bought':
                continue
            if field_name in 'units_sold sell_price sell_commission buy_price buy_commission':
                field_value = str(field_value)
            if field_name == 'profit':
                profit = field_value
                field_value = satoshify(field_value)

            if append:
                field_name += append
            element.findmeld(field_name).content(field_value)

        return profit

    total_profit = 0
    iterator = html_template.findmeld('closed_orders').repeat(closed_orders)

    for element, data in iterator:
        total_profit += render_row(element, data)


    html_template.findmeld('pnl').content(satoshify(total_profit))
    s = html_template.findmeld('closed_orders_sample')
    render_row(s, data, append="2")
    print("HTML OUTFILE: {}".format(html_outfile))
    html_template.write_html(html_outfile)

def main(ini, _date=None):

    config_file = ini

    config = users.read(config_file)
    b = mybittrex.make_bittrex(config)
    report_profit(config_file, b, _date)

if __name__ == '__main__':
    ts = '2017-10-15T21:28:21.05'
    dt = close_date(ts)
    print(dt)
