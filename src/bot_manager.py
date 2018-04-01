from globals import config, log
from prismata_bot import PrismataBot


def main():
    if not config['Passwords']['IRC']:
        log.error("Didn't set up secrets.ini")
        return

    bot = PrismataBot(config['Twitch']['channel'],
                      config['Twitch']['nickname'],
                      config['Twitch']['server'],
                      int(config['Twitch']['port']),
                      config['Passwords']['IRC'])
    bot.start()


if __name__ == '__main__':
    log.info('=== Starting PrismataBot ===')
    main()
