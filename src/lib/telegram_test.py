import unittest

import lib.telegram

class TestMaybeTrade(unittest.TestCase):

    def test_re1(self):
        coin, exchange = lib.telegram.maybe_trade("Coin #BNB on #Binance")
        self.assertEqual(coin.upper(), 'BNB')
        self.assertEqual(exchange.upper(), 'BINANCE')


    def test_re1_1(self):
        coin, exchange = lib.telegram.maybe_trade("Coin #BNB at #Binance")
        self.assertEqual(coin.upper(), 'BNB')
        self.assertEqual(exchange.upper(), 'BINANCE')

    def test_re2(self):
        coin, exchange = lib.telegram.maybe_trade("Buy #BNB")
        self.assertEqual(coin.upper(), 'BNB')
        self.assertFalse(exchange)

    def test_re2_1(self):
        coin, exchange = lib.telegram.maybe_trade("buy #BNB")
        self.assertEqual(coin.upper(), 'BNB')
        self.assertFalse(exchange)


if __name__ == '__main__':
    unittest.main()
