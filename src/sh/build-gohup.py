"""
EDIT the list `invokes` below.
Provide the parser class in src/lib/telegram.py that you want to use
Provide the ini-file in src/users that will connect to the exchange and trade.
"""

class Invoke:

    def __init__(self, parser_class, ini_file):
        self.parser_class = parser_class
        self.ini_file = ini_file

invokes = [
    Invoke('WallStreetCrypto', 'terrence-binance-tb.ini'),
    Invoke('WallStreetTraderSchool', 'terrence-binance-tb.ini'),
    Invoke('TradingCryptoCoach', 'terrence-bittrex-steadyvest.ini')
]

def shell_call(i, nohup=True):
    if nohup:
        _nohup = 'nohup'
        amp = '&'
    else:
        _nohup = ''
        amp = ''

    s = """invoke telegramclient -t {} {}""".format(i.parser_class, i.ini_file)

    if nohup:
        s = """nohup {} > tmp/{}-`date "+%F-%T"`.out &""".format(s, i.parser_class)

    return s + '\n'

with open('gohup', 'w') as gohup:
        for invoke in invokes:
            with open('gohup-init-{}'.format(invoke.parser_class), 'w') as gohup_init:
                gohup.write(shell_call(invoke))
                gohup_init.write(shell_call(invoke, nohup=False))
