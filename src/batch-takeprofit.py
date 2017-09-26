# -*- coding: utf-8 -*-

import inis
INIS = inis.INI

import takeprofit
for ini in INIS.split():
    takeprofit.main(ini)
