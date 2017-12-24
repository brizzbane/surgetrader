#!/usr/bin/env python


# core
import io
import logging
from pprint import pprint, pformat
import traceback

# 3rd party
import meld3
from retry import retry

# local
from ..db import db
from .. import emailer
from .. import mybittrex
from users import users


logger = logging.getLogger(__name__)


def open_order(result):

    # pprint(result['IsOpen'])
    is_open = result['IsOpen']
    # print("\tOrder is open={}".format(is_open))
    return is_open


def close_date(time_string):
    from datetime import datetime
    datetime_format = '%Y-%m-%dT%H:%M:%S'

    time_strings = time_string.split('.')
    _dt = datetime.strptime(time_strings[0], datetime_format)
    return _dt.date()


def percent(a, b):
    return (a/b)*100


def report_profit(user_config_file, exchange, on_date=None):

    user_config = users.read(user_config_file)


    html_template = open('lib/report/profit.html', 'r').read()
    html_template = meld3.parse_htmlstring(html_template)
    html_outfile = open("tmp/" + user_config_file + ".html", 'wb')

    import csv
    csv_file = "tmp/" + user_config_file + ".csv"
    csvfile = open(csv_file, 'w', newline='')
    fieldnames = 'sell_closed buy_opened market units_sold sell_price sell_commission units_bought buy_price buy_commission profit'.split()
    csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    csv_writer.writeheader()

    open_orders = list()
    closed_orders = list()

    for buy in db().select(
        db.buy.ALL,
        orderby=~db.buy.timestamp
    ):
        if buy.config_file != user_config_file:
            #print("config file != {}... skipping".format(user_config_file))
            continue

        if (not buy.sell_id) or (len(buy.sell_id) < 12):
            #print("No sell id ... skipping")
            continue

        print("-------------------{}--------------".format(buy.order_id))


        so = exchange.get_order(buy.sell_id)['result']


        if on_date:
            if open_order(so):
                so['Closed'] = 'n/a'
            else:
                _close_date = close_date(so['Closed'])
                # print("Ondate={}. CloseDate={}".format(pformat(on_date), pformat(_close_date)))

                if type(on_date) is list:
                    if _close_date < on_date[0]:
                        print("Trade is too old for report.")
                        continue
                    elif _close_date > on_date[1]:
                        print("Trade is too new for report.")
                        continue
                elif _close_date != on_date:
                    continue

        # pprint(buy)
        # pprint(so)

        sell_proceeds = so['Price'] - so['CommissionPaid']

        bo = exchange.get_order(buy.order_id)['result']

        buy_proceeds = bo['Price'] + bo['CommissionPaid']

        # print("sell_proceeds={}. buy Order={}. buy proceeds = {}".format(sell_proceeds, bo, buy_proceeds))

        profit = sell_proceeds - buy_proceeds

        print("Sell order={}".format(so))

        if open_order(so):
            p = percent(so['Quantity'] - so['QuantityRemaining'], so['Quantity'])
            so['Quantity'] = "{:d}%".format(int(p))

        calculations = {
            'sell_closed': so['Closed'],
            'buy_opened': bo['Opened'],
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
            del(calculations['sell_commission'])
            del(calculations['sell_price'])
            calculations['sell_closed'] = 'n/a'
            print("\tOpen order...")
            ticker = exchange.get_ticker(so['Exchange'])
            print("Ticker {}".format(ticker))
            if ticker['result']:
                best_bid = ticker['result']['Bid']
                difference = calculations['buy_price'] - best_bid
                calculations['best_bid'] = best_bid
                calculations['difference'] = '{:.2f}'.format(100 * (difference / calculations['buy_price']))
                # print(f"Ticker {ticker}")
                open_orders.append(calculations)
            else:
                raise Exception("Ticker not obtained for {}".format(so))
        else:
            print("\tClosed order: {}".format(calculations))
            if so['PricePerUnit'] is None:
                raise Exception("Order closed but did not sell: {}".format(so))
            csv_writer.writerow(calculations)
            closed_orders.append(calculations)


    # open_orders.sort(key=lambda r: r['difference'])

    html_template.findmeld('acctno').content(user_config_file)
    html_template.findmeld('name').content(user_config.get('client', 'name'))
    html_template.findmeld('date').content("Transaction Log for Previous Day")


    def satoshify(f):
        return '{:.8f}'.format(f)


    def render_row(element, data, append=None):
        for field_name, field_value in data.items():
            if field_name == 'units_bought':
                continue
            if field_name in 'units_sold best_bid sell_price sell_commission buy_price buy_commission':
                field_value = str(field_value)
            if field_name == 'profit':
                profit = field_value
                field_value = satoshify(field_value)

            if append:
                field_name += append

            # print("Field_value={}. Looking for {} in {}".format(field_value, field_name, element))

            element.findmeld(field_name).content(str(field_value))

        return profit

    total_profit = 0
    iterator = html_template.findmeld('closed_orders').repeat(closed_orders)
    for element, data in iterator:
        total_profit += render_row(element, data)

    deposit = float(user_config.get('trade', 'deposit'))
    percent_profit = percent(total_profit, deposit)
    pnl = "{} ({:.2f} % of {})".format(
        satoshify(total_profit), percent_profit, deposit)
    html_template.findmeld('pnl').content(pnl)

    s = html_template.findmeld('closed_orders_sample')
    if not total_profit:
        s.replace("No closed trades!")
    else:
        render_row(s, data, append="2")

    print("Open Orders={}".format(open_orders))
    open_orders_element = html_template.findmeld('open_orders')
    print("Open Orders Element={}".format(vars(open_orders_element)))
    for child in open_orders_element.__dict__['_children']:
        print("\t{}".format(vars(child)))


    iterator = open_orders_element.repeat(open_orders)
    for i, (element, data) in enumerate(iterator):
        data["sell_number"] = i+1
        render_row(element, data, append="3")

    for setting in 'deposit trade top takeprofit preserve'.split():
        elem = html_template.findmeld(setting)
        val = user_config.get('trade', setting)
        # print("In looking for {} we found {} with setting {}".format(
        # setting, elem, val))
        elem.content(val)

    print("HTML OUTFILE: {}".format(html_outfile))
    strfs = io.BytesIO()
    html_template.write_html(html_outfile)
    html_template.write_html(strfs)
    #for output_stream in (html_outfile, strfs):

    return strfs, total_profit

def system_config():
    import configparser
    config = configparser.RawConfigParser()
    config.read("system.ini")
    return config


def notify_admin(msg, user_config, sys_config):

    print(f"Cancelling all open orders before notifying admin about {msg}")

    subject = "SurgeTraderBOT aborted execution on exception"
    sender = sys_config.get('email', 'sender')
    recipient = sys_config.get('email', 'bcc')
    emailer.send(subject,
                 text=msg, html=None,
                 sender=sender,
                 recipient=recipient,
                 bcc=None
                 )
    
    

import json
@retry(exceptions=json.decoder.JSONDecodeError, tries=600, delay=5)
def main(ini, english_date, _date=None, email=True):

    config_file = ini

    user_config = users.read(config_file)
    sys_config = system_config()

    exchange = mybittrex.make_bittrex(user_config)
    try:
        html, total_profit = report_profit(config_file, exchange, _date)
        
        if email:
            subject = "{}'s Profit Report for {}".format(english_date, ini)
            sender = sys_config.get('email', 'sender')
            recipient = user_config.get('client', 'email')
            emailer.send(subject,
                         text='hi my name is slim shady', html=html.getvalue(),
                         sender=sender,
                         recipient=recipient,
                         bcc=sys_config.get('email', 'bcc')
                         )
    
    except Exception as e:
        error_msg = traceback.format_exc()
        print(f'Aborting: {error_msg}')
        if email:
            print("Notifying admin via email")
            notify_admin(error_msg, user_config, sys_config)



if __name__ == '__main__':
    ts = '2017-10-15T21:28:21.05'
    dt = close_date(ts)
    print(dt)
