#!/usr/bin/env python


# core
import io
import json
import logging
import traceback

# 3rd party
from retry import retry
import meld3

# local
import lib.config
import lib.logconfig
from ..db import db
from .. import emailer
from .. import mybittrex


#LOG = logging.getLogger('app')
LOG = lib.logconfig.app_log

def open_order(result):

    # pLOG.debug(result['IsOpen'])
    is_open = result['IsOpen']
    # LOG.debug("\tOrder is open={}".format(is_open))
    return is_open


def close_date(time_string):
    from datetime import datetime
    datetime_format = '%Y-%m-%dT%H:%M:%S'

    time_strings = time_string.split('.')
    _dt = datetime.strptime(time_strings[0], datetime_format)
    return _dt.date()


def percent(a, b):
    return (a/b)*100


class ReportError(Exception):
    """Base class for exceptions in this module."""
    pass


class GetTickerError(ReportError):
    """Exception raised for when exchange does not return a result for a ticker
    (normally due to a network glitch).

    Attributes:
        market -- market in which the error occurred
    """

    def __init__(self, market):
        super().__init__()
        self.market = market
        self.message = "Unable to obtain ticker for {}".format(market)


class NullTickerError(ReportError):
    """Exception raised for when exchange does not return a result for a ticker
    (normally due to a network glitch).

    Attributes:
        market -- market in which the error occurred
    """

    def __init__(self, market):
        super().__init__()
        self.market = market
        self.message = "None price values in ticker for {}".format(market)


def numeric(p):
    if p is None:
        return 0
    return p


@retry(exceptions=GetTickerError, tries=10, delay=5)
def obtain_ticker(exchange, order):
    market = order['Exchange']
    ticker = exchange.get_ticker(market)
    if ticker['result'] is None:
        LOG.debug("Got no result from get_ticker")
        raise GetTickerError(market)

    if ticker['success']:
        if ticker['result']['Bid'] is None:
            raise NullTickerError(market)
        else:
            return ticker
    else:
        raise GetTickerError(market)


@retry(exceptions=json.decoder.JSONDecodeError, tries=3, delay=5)
def obtain_order(exchange, uuid):
    order = exchange.get_order(uuid)
    # LOG.debug("Order = {}".format(order))
    return order['result']


def report_profit(user_config, exchange, on_date=None, skip_markets=None):


    def profit_from(buy_order, sell_order):
        "Calculate profit given the related buy and sell order."

        sell_proceeds = sell_order['Price'] - sell_order['CommissionPaid']
        buy_proceeds = buy_order['Price'] + buy_order['CommissionPaid']
        # LOG.debug("sell_proceeds={}. buy Order={}. buy proceeds = {}".format(sell_proceeds, bo, buy_proceeds))
        profit = sell_proceeds - buy_proceeds
        return profit

    def best_bid(sell_order):
        ticker = obtain_ticker(exchange, sell_order)
        _ = ticker['result']['Bid']
        LOG.debug("ticker = {}".format(ticker))
        return _

    def in_skip_markets(market, skip_markets):
        "Decide if market should be skipped"

        if skip_markets:
            for _skip_market in skip_markets:
                # LOG.debug("Testing {} against {}".format(_skip_market, buy.market))
                if _skip_market in market:
                    LOG.debug("{} is being skipped for this report".format(_skip_market))
                    return True

        return False

    def should_skip(buy_row):
#        if buy_row.config_file != user_config.basename:
#            LOG.debug("\tconfig file != {}... skipping".format(user_config.basename))
#            return True

        if (not buy_row.sell_id) or (len(buy_row.sell_id) < 12):
            LOG.debug("\tNo sell id ... skipping")
            return True

        if in_skip_markets(buy_row.market, skip_markets):
            LOG.debug("\tin {}".format(skip_markets))
            return True

        return False

    html_template = open('lib/report/profit.html', 'r').read()
    html_template = meld3.parse_htmlstring(html_template)
    html_outfile = open("tmp/" + user_config.basename + ".html", 'wb')

    locked_capital = 0

    open_orders = list()
    closed_orders = list()


    query = (db.buy.config_file == user_config.basename)

    for buy in db(query).select(
        db.buy.ALL,
        orderby=~db.buy.timestamp
    ):

        if should_skip(buy):
            LOG.debug("\tSkipping buy order {}".format(buy))
            continue


        LOG.debug("--------------------- {} {}".format(buy.market, buy.order_id))

        so = obtain_order(exchange, buy.sell_id)

        LOG.debug("\t{}".format(so))

        LOG.debug("\tDate checking {} against {}".format(on_date, so['Closed']))

        if on_date:
            if open_order(so):
                LOG.debug("\t\tOpen order")
                so['Closed'] = 'n/a'
            else:
                _close_date = close_date(so['Closed'])
                # LOG.debug("Ondate={}. CloseDate={}".format(pformat(on_date), pformat(_close_date)))

                if type(on_date) is list:
                    if _close_date < on_date[0]:
                        LOG.debug("\t\tTrade is too old for report.")
                        continue
                    elif _close_date > on_date[1]:
                        LOG.debug("\t\tTrade is too new for report.")
                        continue
                elif _close_date != on_date:
                    LOG.debug("\t\tclose date of trade {} != {}".format(_close_date, on_date))
                    continue


        bo = exchange.get_order(buy.order_id)['result']

        LOG.debug("For buy order {}, Sell order={}".format(bo, so))

        if open_order(so):
            so['Quantity'] = "{:d}%".format(int(
                 percent(so['Quantity'] - so['QuantityRemaining'], so['Quantity'])
            ))

        calculations = {
            'sell_closed': so['Closed'],
            'buy_opened': bo['Opened'],
            'market': so['Exchange'],
            'units_sold': so['Quantity'],
            'sell_price': so['PricePerUnit'],
            'sell_commission': so['CommissionPaid'],
            'units_bought': bo['Quantity'],
            'buy_price': numeric(bo['PricePerUnit']),
            'buy_commission': bo['CommissionPaid'],
            'profit': profit_from(bo, so)
        }

        LOG.debug("\tCalculations: {}".format(calculations))
        if open_order(so):
            del calculations['sell_commission']
            del calculations['sell_price']
            calculations['sell_closed'] = 'n/a'
            LOG.debug("\tOpen order...")

            _ = best_bid(so)
            difference = calculations['buy_price'] - _
            calculations['best_bid'] = _
            calculations['difference'] = '{:.2f}%'.format(100 * (difference / calculations['buy_price']))
            open_orders.append(calculations)
            locked_capital += calculations['units_bought'] * calculations['buy_price']

        else:
            LOG.debug("\tClosed order: {}".format(calculations))
            if so['PricePerUnit'] is None:
                raise Exception("Order closed but did not sell: {}\t\trelated buy order={}".format(so, bo))
            closed_orders.append(calculations)


    # open_orders.sort(key=lambda r: r['difference'])

    html_template.findmeld('acctno').content(user_config.filename)
    html_template.findmeld('name').content(user_config.client_name)
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

            # LOG.debug("Field_value={}. Looking for {} in {}".format(field_value, field_name, element))

            element.findmeld(field_name).content(str(field_value))

        return profit

    total_profit = 0
    data = dict()
    iterator = html_template.findmeld('closed_orders').repeat(closed_orders)
    for element, data in iterator:
        total_profit += render_row(element, data)

    deposit = float(user_config.trade_deposit)
    percent_profit = percent(total_profit, deposit)
    pnl = "{} ({:.2f} % of {})".format(
        satoshify(total_profit), percent_profit, deposit)
    html_template.findmeld('pnl').content(pnl)

    s = html_template.findmeld('closed_orders_sample')
    if not total_profit:
        s.replace("No closed trades!")
    else:
        render_row(s, data, append="2")

    LOG.debug("Open Orders={}".format(open_orders))
    open_orders_element = html_template.findmeld('open_orders')
    LOG.debug("Open Orders Element={}".format(vars(open_orders_element)))
    for child in open_orders_element.__dict__['_children']:
        LOG.debug("\t{}".format(vars(child)))


    iterator = open_orders_element.repeat(open_orders)
    for i, (element, data) in enumerate(iterator):
        data["sell_number"] = i+1
        render_row(element, data, append="3")

    for setting in 'deposit trade top takeprofit preserve'.split():
        elem = html_template.findmeld(setting)
        val = user_config.config.get('trade', setting)
        # LOG.debug("In looking for {} we found {} with setting {}".format(
        # setting, elem, val))
        elem.content(val)

    elem = html_template.findmeld('available')
    bal = exchange.get_balance('BTC')['result']
    LOG.debug("bal={}".format(bal))
    btc = bal['Balance']
    val = "Balance={}BTC, Available={}BTC".format(bal['Balance'], bal['Available'])
    elem.content(val)

    elem = html_template.findmeld('locked')
    val = "{}BTC".format(locked_capital)
    elem.content(val)

    elem = html_template.findmeld('operating')
    val = "{}BTC".format(locked_capital + btc)
    elem.content(val)

    LOG.debug("HTML OUTFILE: {}".format(html_outfile))
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


def notify_admin(msg, sys_config):

    LOG.debug("Notifying admin about {}".format(msg))

    subject = "SurgeTraderBOT aborted execution on exception"
    sender = sys_config.email_sender
    recipient = sys_config.email_bcc
    emailer.send(subject,
                 text=msg, html=None,
                 sender=sender,
                 recipient=recipient,
                 bcc=None
                 )



@retry(exceptions=json.decoder.JSONDecodeError, tries=600, delay=5)
def main(config_file, english_date, _date=None, email=True, skip_markets=None):

    LOG.debug("profit.main.SKIP MARKETS={}".format(skip_markets))

    USER_CONFIG = lib.config.User(config_file)
    SYS_CONFIG = lib.config.System()

    exchange = mybittrex.make_bittrex(USER_CONFIG.config)
    try:
        html, _ = report_profit(USER_CONFIG, exchange, _date, skip_markets)

        if email:
            subject = "{}'s Profit Report for {}".format(english_date, config_file)
            emailer.send(subject,
                         text='hi my name is slim shady', html=html.getvalue(),
                         sender=SYS_CONFIG.email_sender,
                         recipient=USER_CONFIG.client_email,
                         bcc=SYS_CONFIG.email_bcc
                         )

    except Exception:
        error_msg = traceback.format_exc()
        LOG.debug('Aborting: {}'.format(error_msg))
        if email:
            LOG.debug("Notifying admin via email")
            notify_admin(error_msg, SYS_CONFIG)



if __name__ == '__main__':
    ts = '2017-10-15T21:28:21.05'
    dt = close_date(ts)
    LOG.debug(dt)
