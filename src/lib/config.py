# -*- coding: utf-8 -*-
"""Provide object-oriented access to the ini files.

SurgeTrader uses a system.ini file and a user ini file. This module provides
OO access to both.
"""

import configparser
import random

class System:

    def __init__(self):
        config = configparser.RawConfigParser()
        with open("system.ini") as file_pointer:
            #config.readfp(f)
            config.read_file(file_pointer)
        self.config = config

    @property
    def users_inis(self):
        _ = self.config.get('users', 'inis').split()
        return _

    @property
    def any_users_ini(self):
        return random.choice(self.users_inis)

    @property
    def ignore_markets_by_in(self):
        _ = self.config.get('ignore', 'coin').split()
        return _

    @property
    def ignore_markets_by_find(self):
        _ = self.config.get('ignore', 'market').split()
        return _

    @property
    def max_open_trades_per_market(self):
        _ = self.config.get('trade', 'per_market')
        return int(_)

    @property
    def min_price(self):
        _ = self.config.get('trade', 'min_price')
        return float(_)

    @property
    def min_volume(self):
        _ = self.config.get('trade', 'min_volume')
        return float(_)

    @property
    def min_gain(self):
        _ = self.config.get('trade', 'min_gain')
        return float(_)

    @property
    def email_bcc(self):
        _ = self.config.get('email', 'bcc')
        return _

    @property
    def email_sender(self):
        _ = self.config.get('email', 'sender')
        return _


class User(System):

    def __init__(self, ini):
        super().__init__()

        config = configparser.RawConfigParser()
        self.filename = "users/" + ini
        self.basename = ini
        with open(self.filename) as file_pointer:
            #config.readfp(f)
            config.read_file(file_pointer)

        self.config = config
        # print("USER CONFIG SECTIONS: {}".format(config._sections))



    @property
    def client_email(self):
        _ = self.config.get('client', 'email')
        return _

    @property
    def client_name(self):
        _ = self.config.get('client', 'name')
        return _

    @property
    def trade_deposit(self):
        _ = self.config.get('trade', 'deposit')
        return float(_)

    @property
    def trade_top(self):
        _ = self.config.get('trade', 'top')
        return int(_)

    @property
    def trade_preserve(self):
        "Return the `preserve` param from the trade section of a user config file."

        _ = self.config.get('trade', 'preserve')
        return float(_)

    @property
    def trade_trade(self):
        "Percentage of seed capital to trade."
        _ = self.config.get('trade', 'trade')
        return float(_)