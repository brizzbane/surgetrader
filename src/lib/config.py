# -*- coding: utf-8 -*-

import configparser
import random

class System:

    def __init__(self):
        config = configparser.RawConfigParser()
        with open("system.ini") as f:
            config.readfp(f)
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
