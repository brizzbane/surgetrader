from pydal import DAL, Field
from datetime import datetime

db = DAL('sqlite://storage.sqlite3')

market = db.define_table(
    'market',
    Field('name'),
    Field('ask', type='double'),
    Field('timestamp', type='datetime', default=datetime.now)
    )

db.executesql('CREATE INDEX IF NOT EXISTS tidx ON market (timestamp);')
db.executesql('CREATE INDEX IF NOT EXISTS m_n_idx ON market (name);')

buy = db.define_table(
    'buy',
    Field('order_id'),
    Field('config_file'),
    Field('market'),
    Field('purchase_price', type='double'),
    Field('selling_price', type='double'),
    Field('sell_id'),
    Field('amount', type='double'),
    Field('timestamp', type='datetime', default=datetime.now)
    )
db.executesql('CREATE INDEX IF NOT EXISTS sidx ON buy (selling_price);')

def recent_buys():
    import inis

    number_of_same_buys = len(inis.INI)

    # 168 hours in a week. Dont buy the same coin for a week
    recency = 168

    relevant_records = recency * number_of_same_buys

    recents = db().select(
        db.buy.ALL,
        orderby=~db.buy.timestamp,
        limitby=(0, number_of_same_buys)
        )

    market_names = [r.market for r in recents]

    print "recent buys: {}".format(market_names)

    return market_names
