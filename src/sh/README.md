
# Useful unix commands

`ps -eaf | grep telegram`

`pkill -f telegram`


# Starting

Run each gohup-init file at the shell so that Telegram can create a session:

    shell> cd surgetrader/src
    shell> bash ./sh/gohup-init-TelegramParserClassName

# Running

Once you have run each init file and entered your phone number and telegram code, then you
can run that client over and over. So once you are ready to run all your clients, just type

    shell> cd surgetrader/src
    shell> ./sh/gohup
