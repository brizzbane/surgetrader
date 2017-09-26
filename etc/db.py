from pydal import DAL, Field
from datetime import datetime

db = DAL('sqlite://download.db')

market = db.define_table(
    'market',
    Field('name')
    )

db.commit()
