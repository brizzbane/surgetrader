
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
    else:
        _nohup = ''

    return """
{} invoke telegramclient -t {} {} > tmp/{}-`date "+%F-%T"`.out &
    """.format(_nohup, i.parser_class, i.ini_file, i.parser_class)

with open('gohup', 'w') as gohup:
    with open('gohup-init', 'w') as gohup_init:
        for invoke in invokes:
            gohup.write(shell_call(invoke))
            gohup_init.write(shell_call(invoke, nohup=False))
