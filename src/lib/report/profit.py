#!/usr/bin/env python


# core
import configparser
import io
import logging
from pprint import pprint

# 3rd party
import meld3

# local
from ..db import db
from .. import mybittrex
from users import users


logger = logging.getLogger(__name__)

def open_order(result):

    pprint(result['IsOpen'])
    return result['IsOpen']

def close_date(time_string):
    from datetime import datetime
    datetime_format = '%Y-%m-%dT%H:%M:%S'

    time_strings = time_string.split('.')
    dt = datetime.strptime(time_strings[0], datetime_format)
    return dt.date()

def percent(a, b):
    return (a/b)*100

def report_profit(config_file, exchange, on_date=None):
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

    open_orders = list()
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

        so = exchange.get_order(buy.sell_id)['result']

        if on_date:
            if open_order(so):
                so['Closed'] = 'n/a'
            else:
                _close_date = close_date(so['Closed'])
                if _close_date != on_date:
                    continue

        pprint(buy)
        pprint(so)

        sell_proceeds = so['Price'] - so['CommissionPaid']

        bo = exchange.get_order(buy.order_id)['result']

        buy_proceeds = bo['Price'] + bo['CommissionPaid']

        pprint("sell_proceeds = {}. buy Order = {}. buy proceeds = {}".format(
            sell_proceeds, bo, buy_proceeds))

        profit = sell_proceeds - buy_proceeds

        if open_order(so):
            p = percent(so['Quantity'] - so['QuantityRemaining'], so['Quantity'])
            so['Quantity'] = "{:d}%".format(int(p))

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

        if open_order(so):
            print("Open order ... skipping")
            open_orders.append(calculations)
        else:
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

            # print("Looking for {} in {}".format(field_name, element))
            element.findmeld(field_name).content(str(field_value))

        return profit

    total_profit = 0
    iterator = html_template.findmeld('closed_orders').repeat(closed_orders)
    for element, data in iterator:
        total_profit += render_row(element, data)



    deposit = float(config.get('trade', 'deposit'))
    percent_profit = percent(total_profit, deposit)
    pnl = "{} ({:.2f} % of {})".format(
        satoshify(total_profit), percent_profit, deposit)
    html_template.findmeld('pnl').content(pnl)

    s = html_template.findmeld('closed_orders_sample')
    if not total_profit:
        s.replace("No closed trades!")
    else:
        render_row(s, data, append="2")

    iterator = html_template.findmeld('open_orders').repeat(open_orders)
    for i, (element, data) in enumerate(iterator):
        data["sell_number"] = i+1
        render_row(element, data, append="3")

    for setting in 'deposit trade top takeprofit preserve'.split():
        elem = html_template.findmeld(setting)
        val = config.get('trade', setting)
        # print("In looking for {} we found {} with setting {}".format(
        # setting, elem, val))
        elem.content(val)

    print("HTML OUTFILE: {}".format(html_outfile))
    strfs = io.BytesIO()
    html_template.write_html(html_outfile)
    html_template.write_html(strfs)
    #for output_stream in (html_outfile, strfs):

    return strfs

def main(ini, english_date, _date=None, email=True):

    config_file = ini

    config = users.read(config_file)
    exchange = mybittrex.make_bittrex(config)
    html = report_profit(config_file, exchange, _date)
    if email:
        from .. import emailer
        subject = "{}'s Profit Report for {}".format(english_date, ini)
        recipient = config.get('client', 'email')
        emailer.send(subject, None, html.getvalue(), recipient)

if __name__ == '__main__':
    ts = '2017-10-15T21:28:21.05'
    dt = close_date(ts)
    print(dt)
