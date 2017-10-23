from marrow.mailer import Mailer, Message

def send(subject, txt, html, recipient, cc=None):

    mailer = Mailer(
        dict(
            transport = dict(
                use = 'smtp',
                host = 'localhost')))

    mailer.start()

    message = Message(
        author="SurgeTrader@TerrenceBrannon.com",
        to=recipient,
        cc=cc,
        bcc='revshareworks@gmail.com'
    )

    message.subject = subject
    message.rich = html
    message.plain = 'txt'

    mailer.send(message)
    mailer.stop()
