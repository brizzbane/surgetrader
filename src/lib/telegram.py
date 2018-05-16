"""
shell> cd surgetrader/src ; python -m 'lib.telegram_test'

"""

# core
import re

# 3rd party
import argh
from pyrogram import Client
from pyrogram.api import types

# local
import lib.buy
import lib.logconfig
import lib.takeprofit


LOG = lib.logconfig.app_log

# https://t.me/PyrogramChat

def ccxt_symbol(base,quote):
    return "{}/{}".format(base, quote)

class TelegramClient(object):

    def __init__(self, exchange_label):
        self.exchange_label = exchange_label

    def make_update_handler(self, user_configo):

        def update_handler(client, update, users, chats):
            LOG.debug("<UPDATE_HANDLER update={}>".format(update))

            if isinstance(update, types.UpdateUserStatus):
                LOG.debug("Ignoring...")
                return
            elif isinstance(update, types.UpdateChatUserTyping):
                LOG.debug("Ignoring...")
                return
            elif isinstance(update, types.UpdateReadHistoryInbox):
                LOG.debug("Ignoring...")
                return
            elif isinstance(update, types.UpdateEditChannelMessage):
                LOG.debug("Ignoring...")
                return
            elif (
                    isinstance(update, types.UpdateEditChannelMessage) and
                    update.message._ == "types.MessageService"
            ):
                LOG.debug("Ignoring")
                return

            try:
                message = update.message
            except AttributeError:
                LOG.debug("Attribute error on {}".format(update))
                return

            # TODO
            # if message.to_id == "pyrogram.api.types.PeerUser":
            #     LOG.debug("Ignoring...")
            #     return

            i = message.to_id.channel_id
            if i in self.CHANNELS.values():
                LOG.debug("** MESSAGE FROM RELEVANT CHANNEL:")
                LOG.debug(message.message)
                (coin, exchange) = self.maybe_trade(message.message)
                if not coin:
                    LOG.debug("\tNot a trade message")
                else:
                    market = "BTC-{}".format(coin)
                    market = ccxt_symbol(coin, 'BTC')
                    LOG.debug("\tTrade {} with ini={}.".format(market, user_configo))

                    lib.buy.process2(user_configo, self.exchange_label, [market])
                    lib.takeprofit.take_profit(user_configo)
            else:
                LOG.debug("Message is not from desired channel:")
                # LOG.debug(message)

            LOG.debug("</UPDATE_HANDLER>")

        return update_handler


class TradingCryptoCoach(TelegramClient):

    # 'easycoinpicks'      : 1312304347, # My Test Channel,
    CHANNELS = {

            'Tradingcryptocoach' : 1147798110  # https://t.me/Tradingcryptocoach
            }

    def maybe_trade(self, message):
        # match "Coin #XVG"
        re0 = re.compile(r'^Coin\s+#(\S+)', re.IGNORECASE)

        # match #SYS Coin at #Bittrex
        # match #WAVES dip looks good
        re1 = re.compile(r'^#(\S+)\s+(at|Coin|Dip)(\s+\S+\s+#?(\S+))?', re.IGNORECASE)

        # match "Buy #XVG' or Accumulate #EXCL at #Bittrex
        # note: He sometimes says Accumulate Some #GAME and the `some` throws me off
        re2 = re.compile(r'^(Buy|Accumulate)\s+#(\S+)', re.IGNORECASE)

        # match Buy and Hold #CRW
        re2a = re.compile(r'^Buy\s+and\s+Hold\s+#(\S+)', re.IGNORECASE)

        # match "#XVG Buy'
        re3 = re.compile(r'^#(\S+)\s+Buy', re.IGNORECASE)
        m = re3.match(message)
        if m:
            coin = m.group(1)
            return coin, None


        # match "#XVG at Bittrex'
        re4 = re.compile(r'^#(\S+)\s+at\s+Bittrex', re.IGNORECASE)

        m = re0.search(message)
        if m:
            coin = m.group(1)
            return coin, None

        m = re1.search(message)
        if m:
            coin = m.group(1)
            return coin, None

        m = re2.search(message)
        if m:
            coin = m.group(2)
            return coin, None

        m = re2a.search(message)
        if m:
            coin = m.group(1)
            return coin, None


        m = re3.match(message)
        if m:
            coin = m.group(1)
            return coin, None

        m = re4.match(message)
        if m:
            coin = m.group(1)
            return coin, None


        return None, None


class QualitySignals(TelegramClient):

    # 'easycoinpicks'         : 1312304347, # My Test Channel,
    CHANNELS = {

        'QualitySignalsChannel' : 1343688547 # https://t.me/QualitySignalsChannel
        # 'QualitySignals'        : 1226119909  #
    }


    def maybe_trade(self, message):

        # match #SYS Coin at #Bittrex
        re1 = re.compile(
            r'#(\S+)\s+at\s+({})'.format(self.exchange_label),
            re.IGNORECASE|re.MULTILINE|re.DOTALL
        )

        m = re1.search(message)
        if m:
            coin, exchange = m.groups()
            return coin, exchange

        return None, None

class WallStreetTraderSchool(TelegramClient):

    # 'easycoinpicks'      : 1312304347,   # My Test Channel,
    CHANNELS = {

        'WallStreetTraderSchool'   : 1136730358
    }


    def maybe_trade(self, message):

        # match "#BCPT\n\nBuy @5200\n\nSell @ 5650, 6100, 6600"
        re1 = re.compile(
            r'#(\S+).+Buy'.format(self.exchange_label),
            re.IGNORECASE|re.MULTILINE|re.DOTALL
        )

        m = re1.search(message)
        if m:
            coin = m.group(1)
            return coin, None

        # match Buy INS
        re1 = re.compile(
            r'Buy (\S+)',
            re.IGNORECASE|re.MULTILINE|re.DOTALL
        )

        m = re1.search(message)
        if m:
            coin = m.group(1)
            return coin, None


        return None, None


class WallStreetCrypto(TelegramClient):

    # 'easycoinpicks'      : 1312304347,   # My Test Channel,
    CHANNELS = {

        'WallStreetCrypto'   : 1275581291
    }


    def maybe_trade(self, message):

        # match "TRX looking good. Huge buy wall looks like whale accumulating before another bull run."
        re1 = re.compile(
            r'(\S+)\s+looking\s+good',
            re.IGNORECASE|re.MULTILINE|re.DOTALL
        )

        m = re1.search(message)
        if m:
            coin = m.group(1)
            return coin, None

        return None, None



def make_chat_parser(telegram_class, exchange_label):
    _ = eval("{}('{}')".format(telegram_class, exchange_label))
    return _


def main(telegram_class, user_configo, session_label):

    LOG.debug("C={} I={}".format(telegram_class, user_configo))

    client = Client(session_name=session_label)

    chat_parser = make_chat_parser(telegram_class, user_configo.exchange)

    update_handler = chat_parser.make_update_handler(user_configo)

    LOG.debug("client={}. chat_parser={}. update_handler={}".format(client, chat_parser, update_handler))

    from pyrogram import RawUpdateHandler

    client.add_handler(RawUpdateHandler(update_handler))
    client.start()

    for channel in chat_parser.CHANNELS.keys():
        client.join_chat(channel)



if __name__ == '__main__':
    argh.dispatch_command(main)
