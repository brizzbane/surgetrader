from invoke import task




def listify_ini(ini):
    if ini:
        inis = [ini]
    else:
        from users import users
        inis = users.inis()

    return inis






@task
def profitreport(_ctx, ini=None, date_string=None):
    import lib.report.profit

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
            d = today - relativedelta(months=1)
            startOfLastMonth = date(d.year, d.month, 1)
            endOfLastMonth = date(today.year, today.month, 1) - relativedelta(days=1)
            print("Date range for profit report. Start={}. End={}".format(
                    startOfLastMonth, endOfLastMonth))
            _date = [startOfLastMonth, endOfLastMonth]
        else:
            raise Exception("Unrecognized date option")
    else:
        _date = None

    for user_ini in inis:
        print("Processing {}".format(user_ini))
        profit, config = lib.report.profit.main(user_ini, date_string, _date)


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
def clearprofit(_ctx, ini=None):
    from lib import takeprofit as _takeprofit

    inis = listify_ini(ini)

    for _ in inis:
        print("Processing {}".format(_))
        _takeprofit.clear_profit(_)
        
        
@task
def sellall(_ctx, ini):
    from lib import sellall as _sellall

    _sellall.main(ini)
