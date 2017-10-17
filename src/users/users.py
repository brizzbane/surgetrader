# -*- coding: utf-8 -*-

# ini-terrence.brannon@gmail.ini
# ini-steadyvest.radar.ini
# ini-steadyvest.strategic.ini
# ini-msamitech@yahoo.ini


INIS = """
ini-steadyvest@protonmail.ini
agnes.ini
ini-mikegardner936@gmail.ini
"""

def inis():
    return INIS.split()

def read(ini):
    import configparser
    config = configparser.RawConfigParser()
    config.read("users/" + ini)
    return config
