class Abstract(ccxt):
            
    def bind_keys(self, exchange, configo):
        exchange.apikey = configo.apikey
        exchange.secret = configo.secret
        
    def from_config(self, configo):

        exchange_label = configo.exchange
        
        if exchange_label == 'binance':
            import lib.exchange.binance
            e = lib.exchange.binance.Binance()
            
        elif exchange_label == 'bittrex':
            import lib.exchange.bittrex
            e = lib.exchange.binance.Bittrex()
            
        else:
            raise Exception("Unknown exchange label.")

        self.bind_keys(e, configo)
        return e

