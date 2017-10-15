# -*- coding: utf-8 -*-

# ini-terrence.brannon@gmail.ini
# ini-steadyvest.radar.ini
# ini-steadyvest.strategic.ini
# ini-msamitech@yahoo.ini


INIS = """
ini-mikegardner936@gmail.ini
ini-steadyvest@protonmail.ini
"""

def inis():
    return INIS.split()

def read(ini):
    import configparser
    config = configparser.RawConfigParser()
    config.read("users/" + ini)
    return config
