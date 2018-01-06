"""Define a collection of tasks invokable from the command-line/cron.

This module leverages `PyInvoke`_ to create tasks relevant ot the execution
of SurgeTrader.

Example:


        $ invoke download

Todo:
    * For module TODOs
    * You have to also use ``sphinx.ext.todo`` extension

.. _PyInvoke:
   http://www.pyinvoke.org/
"""

from invoke import task


def listify_ini(ini):
    """Coerce the ini argument to a list of 1+ ini-file names.

    When provided with a value V, return a list consisting solely of V.
    When no value is provided, return a list consisting of the ini files of
    all active users:

    Args:
        ini (str): The name of an ini file or a falsy value.

    Returns:
        A list of 1+ ini-file names

    """
    if ini:
        inis = [ini]
    else:
        from users import users
        inis = users.inis()

    return inis


@task
def profitreport(_ctx, ini=None, date_string=None, skip_markets=None):
    """Generate and email a profit report for a certain time frame.

    Args:
        ini (str): The name of an ini file or a falsy value.
        date_string : "yesterday" and "lastmonth" are valid values
        skip_markets: Coins to exclude from calculating the profit report.
            This is used when a market is under maintenance becauase at that
            point the exchange API does not return data for that coin.

    Returns:
        Nothing. It dumps a csv and html of the email profit report in src/tmp.

    """
    import lib.report.profit


    print("tasks.SKIP MARKETS={}".format(skip_markets))


    inis = listify_ini(ini)

    if date_string:
        from datetime import date
        if date_string == 'yesterday':
            date_string = "Yesterday"
            _date = date.fromordinal(date.today().toordinal()-1)
        elif date_string == 'lastmonth':
            date_string = "Last month"
            from dateutil.relativedelta import relativedelta
            today = date.today()
            diff = today - relativedelta(months=1)
            start_of_last_month = date(diff.year, diff.month, 1)
            end_of_last_month = date(today.year, today.month, 1) - relativedelta(days=1)
            print("Date range for profit report. Start={}. End={}".format(
                start_of_last_month, end_of_last_month))
            _date = [start_of_last_month, end_of_last_month]
        else:
            raise Exception("Unrecognized date option")
    else:
        _date = None

    if skip_markets:
        skip_markets = skip_markets.split()

    print("tasks2.SKIP MARKETS={}".format(skip_markets))

    for user_ini in inis:
        print("Processing {}".format(user_ini))
        lib.report.profit.main(user_ini, date_string, _date=_date, skip_markets=skip_markets)


@task
def download(_ctx):
    import random
    from users import users
    from lib import download as _download

    _download.main(random.choice(users.inis()))


@task
def buy(_ctx, ini=None):
    from lib import buy as _buy

    inis = listify_ini(ini)
    _buy.main(inis)


@task
def takeprofit(_ctx, ini=None):
    from lib import takeprofit as _takeprofit

    inis = listify_ini(ini)

    for _ in inis:
        print("Processing {}".format(_))
        _takeprofit.take_profit(_)


@task
def cancelsells(_ctx, ini=None):
    from lib import takeprofit as _takeprofit

    inis = listify_ini(ini)

    for _ in inis:
        print("Processing {}".format(_))
        _takeprofit.clear_profit(_)


@task
def sellall(_ctx, ini):
    from lib import sellall as _sellall

    _sellall.main(ini)
