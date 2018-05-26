import unittest

import lib.telegram

# shell> cd surgetrader/src
# shell> python -m lib.telegram_test


class TestCryptoAddicts(unittest.TestCase):

    def setUp(self):

        telegram_class = 'CryptoAddicts'
        exchange_label = 'binance'
        self.chat_parser = lib.telegram.make_chat_parser(telegram_class, exchange_label)
        self.photo_message = {
            "_": "Message",
            "message_id": 4109,
            "date": 1527344286,
            "chat": {
                "_": "Chat",
                "id": -1001139894217,
                "type": "channel",
                "title": "CRYPTO-ADDICTS Alerts & Analys",
                "username": "crypto_addicts_free",
                "photo": {
                    "_": "ChatPhoto",
                    "small_file_id": "AQADBAATQPmNGgAEDz49j3KrtSwAATEFAAEC",
                    "big_file_id": "AQADBAATQPmNGgAEVwb8xX1fmXQCMQUAAQI"
                }
            },
            "edit_date": 1527344301,
            "photo": [
                {
                    "_": "PhotoSize",
                    "file_id": "AgADBAADKa0xG0WoSVDRe_f7mwO8W5TonhoABEGGCO8uUcGDhzEAAgI",
                    "width": 90,
                    "height": 57,
                    "file_size": 1116,
                    "date": 1527344213
                },
                {
                    "_": "PhotoSize",
                    "file_id": "AgADBAADKa0xG0WoSVDRe_f7mwO8W5TonhoABEli-6yh5NKPiDEAAgI",
                    "width": 320,
                    "height": 202,
                    "file_size": 18680,
                    "date": 1527344213
                },
                {
                    "_": "PhotoSize",
                    "file_id": "AgADBAADKa0xG0WoSVDRe_f7mwO8W5TonhoABLGzn8roZezpiTEAAgI",
                    "width": 800,
                    "height": 504,
                    "file_size": 86075,
                    "date": 1527344213
                },
                {
                    "_": "PhotoSize",
                    "file_id": "AgADBAADKa0xG0WoSVDRe_f7mwO8W5TonhoABIINhAFLlrQ5hjEAAgI",
                    "width": 912,
                    "height": 574,
                    "file_size": 107038,
                    "date": 1527344213
                }
            ],
            "caption": "\ud83d\ude80 ANT/BTC\n\nExchange:Bittrex \nBuy Below 42250\nStop 40600\nT1# 42700 - T2# 43306 - T3# 44600\n\n\ud83d\udd38 Period: 19h - Risk: 3.8/5",
            "views": 21,
            "outgoing": False
        }


    def test_re1(self):
        coin, exchange = self.chat_parser.maybe_trade(self.photo_message['caption'])

        self.assertEqual(coin.upper(), 'ANT')



class TestCryptoCoach(unittest.TestCase):

    def setUp(self):

        telegram_class = 'TradingCryptoCoach'
        exchange_label = 'bittrex'
        self.chat_parser = lib.telegram.make_chat_parser(telegram_class, exchange_label)

    def test_re0(self):
        text = 'Coin #STEEM'
        coin, exchange = self.chat_parser.maybe_trade(text)
        self.assertEqual(coin.upper(), 'STEEM')

    def test_re1(self):
        text = '#SYS Coin at Bittrex'
        coin, exchange = self.chat_parser.maybe_trade(text)

        self.assertEqual(coin.upper(), 'SYS')

    def test_re2(self):
        text = 'Buy #XVG'
        coin, exchange = self.chat_parser.maybe_trade(text)

        self.assertEqual(coin.upper(), 'XVG')


    def test_re2_a(self):
        text = 'Accumulate #LTC'
        coin, exchange = self.chat_parser.maybe_trade(text)

        self.assertEqual(coin.upper(), 'LTC')

    def test_re2_b(self):
        text = 'Accumulate some #XVG'
        coin, exchange = self.chat_parser.maybe_trade(text)

        self.assertEqual(coin.upper(), 'XVG')

    def test_re2a(self):
        text = 'Buy and Hold #CRW guys till 16th of May 🚀🚀🚀'
        coin, exchange = self.chat_parser.maybe_trade(text)

        self.assertEqual(coin.upper(), 'CRW')

    def test_re3(self):
        text = '#ETH buy'
        coin, exchange = self.chat_parser.maybe_trade(text)

        self.assertEqual(coin.upper(), 'ETH')

    def test_re4(self):
        text = '#XRP at Bittrex'
        coin, exchange = self.chat_parser.maybe_trade(text)

        self.assertEqual(coin.upper(), 'XRP')


if __name__ == '__main__':
    unittest.main()
