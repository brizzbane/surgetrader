import unittest

import lib.telegram

class TestQualitySignals(unittest.TestCase):

    def setUp(self):
        self.channel_text = """Signal 2455 (42º today) at 18-Apr 17:46 UTC

#NEBL at BINANCE - Chart (https://www.binance.com/trade.html?symbol=NEBL_BTC)

Buy:   0.00127433 - 0.00130007
Current ask: 0.00128730
Target 1:  0.00149000 (15.75%)
Target 2:  0.00166000 (28.95%)
Target 3:  0.00181000 (40.60%)
Type:   SHORT/MID TERM

LAST:0.00128720 2.89%
ASK: 0.00128730 BID: 0.00128720
LOW: 0.00121500 HIGH:0.00128720
"""    

        telegram_class = 'QualitySignals'
        exchange_label = 'binance'
        self.chat_parser = lib.telegram.make_chat_parser(telegram_class, exchange_label)
    
    def test_re1(self):
        coin, exchange = self.chat_parser.maybe_trade(self.channel_text)

        self.assertEqual(coin.upper(), 'NEBL')
        self.assertEqual(exchange.upper(), 'BINANCE')


if __name__ == '__main__':
    unittest.main()
