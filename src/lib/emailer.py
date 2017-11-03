from marrow.mailer import Mailer, Message


def send(subject, _txt, html, sender, recipient, cc=None, bcc=None):

    mailer = Mailer(
        dict(
            transport=dict(
                use='smtp',
                host='localhost')))

    mailer.start()

    message = Message(
        author=sender,
        to=recipient,
        cc=cc,
        bcc=bcc
    )

    message.subject = subject
    message.rich = html
    message.plain = 'txt'

    mailer.send(message)
    mailer.stop()
