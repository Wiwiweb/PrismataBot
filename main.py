from difflib import get_close_matches
from difflib import SequenceMatcher
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import sys

from configparser import ConfigParser
import irc.bot

CONFIG_FILE = "cfg/config.ini"
SECRETS_FILE_PRIVATE = "cfg/secrets.ini"
config = ConfigParser()
config.read([CONFIG_FILE, SECRETS_FILE_PRIVATE])

log = logging.getLogger('PrismataBot')
file_handler = TimedRotatingFileHandler(config['Files']['logfile'], 'midnight')
file_handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s - %(message)s'))
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
log.addHandler(file_handler)
log.addHandler(console_handler)
log.setLevel(logging.DEBUG)

tooltips = json.load(open(config['Files']['unit_tooltips']))

class PrismataBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port, password):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, password)], nickname, nickname)
        self.channel = channel

    def on_welcome(self, connection, event):
        log.info('Connected to Twitch IRC server')
        connection.join(self.channel)

    def on_join(self, connection, event):
        log.info('Joined channel ' + self.channel)

    def on_pubmsg(self, connection, event):
        msg = event.arguments[0].split(' ', 1)
        if len(msg) == 2 and len(msg[1]) > 0 and (msg[0].startswith('!unit') or msg[0].startswith('!prismata')):
            self.answer_command(connection, msg[1])

    def on_disconnect(self, connection, event):
        log.info('Disconnected (channel ' + self.channel + ')')
        raise SystemExit()

    def answer_command(self, connection, query):
        log.info('Answering !unit ' + query)
        tooltip_key = get_close_matches(query, tooltips.keys(), 1, 0.3)
        if tooltip_key:
            tooltip_key = tooltip_key[0]
            log.debug('Closest match: {} with {}'.format(tooltip_key, SequenceMatcher(None, query, tooltip_key).ratio()))
            connection.privmsg(self.channel, '{}: {}'.format(tooltip_key, tooltips[tooltip_key]))
        else:
            log.debug('Not found')
            connection.privmsg(self.channel, "Couldn't find a unit for {}!".format(query))


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
