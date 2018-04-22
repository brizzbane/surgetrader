import ccxt


class Abstract:
            
    @classmethod
    def bind_keys(cls, exchange, configo):
        exchange.apikey = configo.apikey
        exchange.secret = configo.secret
        
    @classmethod
    def factory(cls, configo, exchange_label):
        
        if exchange_label == 'binance':
            import lib.exchange.binance
            e = lib.exchange.binance.Binance()
            
        elif exchange_label == 'bittrex':
            import lib.exchange.bittrex
            e = lib.exchange.binance.Bittrex()
            
        else:
            raise Exception("Unknown exchange label.")

        cls.bind_keys(e, configo)
        return e

