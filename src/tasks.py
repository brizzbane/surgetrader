from invoke import task


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
            print("Not implemented")
            quit()
        else:
            raise Exception("Unrecognized date option")
    else:
        _date = None

    for _ini in inis:
        print("Processing {}".format(_ini))
        lib.report.profit.main(_ini, date_string, _date)


@task
def download(_ctx):
    import random
    from users import users
    from lib import download as _download

    _download.main(random.choice(users.inis()))


def listify_ini(ini):
    if ini:
        inis = [ini]
    else:
        from users import users
        inis = users.inis()

    return inis


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
        _takeprofit.main(_)


@task
def sellall(_ctx, ini):
    from lib import sellall as _sellall

    _sellall.main(ini)
