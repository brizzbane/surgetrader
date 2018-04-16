import unittest

import lib.telegram

class TestMaybeTrade(unittest.TestCase):

    def test_re1(self):
        coin, exchange = lib.telegram.maybe_trade("Coin #BNB on #Binance")
        self.assertEqual(coin.upper(), 'BNB')
        self.assertEqual(exchange.upper(), 'BINANCE')

    def test_re1_1(self):
        coin, exchange = lib.telegram.maybe_trade("#SYS Coin at #Binance")
        self.assertEqual(coin.upper(), 'SYS')
        self.assertEqual(exchange.upper(), 'BINANCE')

    def test_re2(self):
        coin, exchange = lib.telegram.maybe_trade("Buy #BNB")
        self.assertEqual(coin.upper(), 'BNB')
        self.assertFalse(exchange)

        coin, exchange = lib.telegram.maybe_trade("Buy #ABY (ArtByte) at Bittrex")
        self.assertEqual(coin.upper(), 'ABY')
        self.assertFalse(exchange)

        coin, exchange = lib.telegram.maybe_trade("Accumulate #BNB")
        self.assertEqual(coin.upper(), 'BNB')
        self.assertFalse(exchange)

    def test_re3(self):
        coin, exchange = lib.telegram.maybe_trade("buy #BNB")
        self.assertEqual(coin.upper(), 'BNB')
        self.assertFalse(exchange)


if __name__ == '__main__':
    unittest.main()
