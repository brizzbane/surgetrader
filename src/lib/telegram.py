# core
from datetime import datetime
import re

# 3rd party
from pyrogram import Client
from pyrogram.api import types

# local
import lib.buy
import lib.logconfig


LOG = lib.logconfig.app_log


# Trading Crypto Coach's Channel ID
CHANNEL_ID = 1147798110

# My Test Channel ID
TEST_CHANNEL_ID = 1312304347

client = Client(session_name="example")

def maybe_trade(message):
    # match "Coin #XVG on #Bittrex"
    re1 = re.compile(r'Coin\s+#(\S+)\s+\S+\s+#(\S+)', re.IGNORECASE)

    # match "Buy #XVG'
    re2 = re.compile(r'Buy\s+#(\S+)', re.IGNORECASE)

    m = re1.search(message)
    if m:
        coin, exchange = m.groups()
        return coin, exchange

    m = re2.match(message)
    if m:
        coin = m.group(1)
        return coin, None

    return None, None


def make_update_handler(inis):

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

        try:
            message = update.message
        except AttributeError:
            LOG.debug("Attribute error on {}".format(update))
            return

        i = message.to_id.channel_id
        if i == CHANNEL_ID or i == TEST_CHANNEL_ID:
            LOG.debug("** MESSAGE FROM RELEVANT CHANNEL:")
            LOG.debug(message.message)
            (coin, exchange) = maybe_trade(message.message)
            if not coin:
                LOG.debug("\tNot a trade message")
            else:
                for ini in inis:
                    market = "BTC-{}".format(coin)
                    LOG.debug("\tTrade {} on {} with ini={}.".format(market, exchange, ini))

                    lib.buy.process(ini, [market])
        else:
            LOG.debug("Message is not from desired channel:")
            # LOG.debug(message)

        LOG.debug("</UPDATE_HANDLER>")

    return update_handler


def main(inis):

    update_handler = make_update_handler(inis)

    client.set_update_handler(update_handler)

    client.start()

    client.join_chat('Tradingcryptocoach')
    client.join_chat('easycoinpicks')




if __name__ == '__main__':
    argh.dispatch_command(main)
