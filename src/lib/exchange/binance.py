import ccxt.binance


class Binance(ccxt.binance):

    def filled(self, order):
        return order['info']['status'] == 'FILLED'
