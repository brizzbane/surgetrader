from invoke import task


@task
def download(ctx, ini=None):
    import random
    from users import users
    from lib import download

    download.main(random.choice(users.inis()))

def listify_ini(ini):
    if ini:
        inis = [ini]
    else:
        from users import users
        inis = users.inis()

    return inis

@task
def buy(ctx, ini=None):
    from users import users
    from lib import buy

    inis = listify_ini(ini)
    buy.main(inis)

@task
def takeprofit(ctx, ini=None):
    from lib import takeprofit

    inis = listify_ini(ini)

    for ini in inis:
        print("Processing {}".format(ini))
        takeprofit.main(ini)

@task
def profitreport(ctx, ini=None, d=None):
    import lib.report.profit

    inis = listify_ini(ini)

    # TODO parse d for yesterday, today, or general date
    # TODO parse d for yesterday, lastmonth
    if d:
        from datetime import date
        _date = date.fromordinal(date.today().toordinal()-1)
    else:
        _date = None

    for ini in inis:
        print("Processing {}".format(ini))
        lib.report.profit.main(ini, _date)


@task
def sellall(ctx, ini):
    from lib import sellall

    sellall.main(ini)
