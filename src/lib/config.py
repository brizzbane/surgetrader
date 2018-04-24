# -*- coding: utf-8 -*-
"""Provide object-oriented access to the ini files.

SurgeTrader uses a system.ini file and a user ini file. This module provides
OO access to both.
"""

# core
import random

# 3rd party
from configobj import ConfigObj

# local


class System:

    def __init__(self):
        config = ConfigObj("system.ini")
        self.config = config

    @property
    def users_inis(self):
        _ = self.config['users']['inis'].split()
        return _

    @property
    def any_users_ini(self):
        return random.choice(self.users_inis)

    @property
    def ignore_markets_by_in(self):
        _ = self.config['ignore']['coin'].split()
        return _

    @property
    def ignore_markets_by_find(self):
        _ = self.config['ignore']['market'].split()
        return _

    @property
    def max_open_trades_per_market(self):
        _ = self.config['trade']['per_market']
        return int(_)

    @property
    def min_price(self):
        _ = self.config['trade']['min_price']
        return float(_)

    @property
    def min_volume(self):
        _ = self.config['trade']['min_volume']
        return float(_)

    @property
    def min_gain(self):
        _ = self.config['trade']['min_gain']
        return float(_)

    @property
    def email_bcc(self):
        _ = self.config['email']['bcc']
        return _

    @property
    def email_sender(self):
        _ = self.config['email']['sender']
        return _


class User(System):

    def __init__(self, ini, exchange_section, exchange_subsection):
        self.system = System()

        self.filename = "users/{}".format(ini)
        self._exchange_section = exchange_section
        self._exchange_subsection = exchange_subsection

        self.config = ConfigObj(self.filename)
        self.config_name = ini
        # print("USER CONFIG SECTIONS: {}".format(config._sections))

    @classmethod
    def from_string(cls, ini_string):
        user_ini, exchange_section, exchange_subsection = ini_string.split("/")
        instance = User(user_ini, exchange_section, exchange_subsection)
        return instance

    def exchange_section(self, parameter):
        _ = self.config[self._exchange_section][parameter]
        return _

    def exchange_subsection(self, parameter):
        _ = self.config[self._exchange_section][self._exchange_subsection][parameter]
        return _

    @property
    def client_email(self):
        _ = self.config['client']['email']
        return _

    @property
    def client_name(self):
        _ = self.config['client']['name']
        return _

    @property
    def trade_deposit(self):
        _ = self.exchange_subsection('deposit')
        return float(_)

    @property
    def trade_top(self):
        _ = self.exchange_subsection('top')
        return int(_)


    @property
    def trade_preserve(self):
        "Return the `preserve` param from the trade section of a user config file."

        _ = self.exchange_subsection('preserve')
        return float(_)
    
    @property
    def apikey(self):
        _ = self.exchange_subsection('apikey')
        return _

    @property
    def secret(self):
        _ = self.exchange_subsection('secret')
        return _

    @property
    def trade(self):
        "Percentage of seed capital to trade."
        _ = self.exchange_subsection('trade')
        return float(_)

    @property
    def take_profit(self):
        "Percentage of seed capital to trade."
        _ = self.exchange_subsection('takeprofit')
        return float(_)
