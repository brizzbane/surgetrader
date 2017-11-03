from marrow.mailer import Mailer, Message

# The profit report email will come from this person
MAIL_SENDER = "SurgeTrader@TerrenceBrannon.com"
MAIL_BCC="revshareworks@gmail.com"

def send(subject, txt, html, recipient, cc=None):

    mailer = Mailer(
        dict(
            transport = dict(
                use = 'smtp',
                host = 'localhost')))

    mailer.start()

    message = Message(
        author=MAIL_SENDER,
        to=recipient,
        cc=cc,
        bcc=MAIL_BCC
    )

    message.subject = subject
    message.rich = html
    message.plain = 'txt'

    mailer.send(message)
    mailer.stop()
