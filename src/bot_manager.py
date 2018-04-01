from globals import config, log
from prismata_bot import PrismataBot


def start_bot(channel):
    bot = PrismataBot(config['Twitch']['nickname'],
                      config['Twitch']['server'],
                      int(config['Twitch']['port']),
                      config['Passwords']['IRC'])
    bot.join_channel(channel)
    bot.start()


def main():
    if not config['Passwords']['IRC']:
        log.error("Didn't set up secrets.ini")
        return
    start_bot(config['Twitch']['channel'])

if __name__ == '__main__':
    log.info('=== Starting PrismataBot ===')
    main()
