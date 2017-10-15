from invoke import task

@task
def download(ctx, ini=None):
    import random
    from users import users
    from lib import download

    download.main(random.choice(users.inis()))

@task
def buy(ctx, ini=None):
    from users import users
    from lib import buy
    buy.main(users.inis())

@task
def takeprofit(ctx, ini=None):
    from lib import takeprofit

    if ini:
        inis = [ini]
    else:
        from users import users
        inis = users.inis()

    for ini in inis:
        print("Processing {}".format(ini))
        takeprofit.main(ini)

@task
def profitreport(ctx, ini=None):
    import lib.report.profit

    if ini:
        inis = [ini]
    else:
        from users import users
        inis = users.inis()

    for ini in inis:
        print("Processing {}".format(ini))
        lib.report.profit.main(ini)


@task
def sellall(ctx, ini):
    from lib import sellall

    sellall.main(ini)
