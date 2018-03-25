from configparser import ConfigParser
import irc.bot

CONFIG_FILE = "cfg/config.ini"
SECRETS_FILE_PRIVATE = "cfg/secrets.ini"
config = ConfigParser()
config.read([CONFIG_FILE, SECRETS_FILE_PRIVATE])


class PrismataBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port, password):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, password)], nickname, nickname)
        self.channel = channel

    def on_welcome(self, connection, event):
        print('connected')
        connection.join(self.channel)

    def on_join(self, connection, event):
        print('joined')

    def on_pubmsg(self, connection, event):
        msg = event.arguments[0].split(' ', 1)
        if len(msg) == 2 and len(msg[1]) > 0 and (msg[0].startswith('!unit') or msg[0].startswith('!prismata')):
            self.printPrismataUnit(connection, msg[1])

    def on_disconnect(self, connection, event):
        print('disconnected: ' + event.arguments[0])
        raise SystemExit()

    def printPrismataUnit(self, connection, query):
        connection.privmsg(self.channel, "You asked for this: " + query)


def main():
    if not config['Passwords']['IRC']:
        print("Didn't set up secrets.ini")
        return
    bot = PrismataBot(config['Twitch']['channel'],
                      config['Twitch']['nickname'],
                      config['Twitch']['server'],
                      int(config['Twitch']['port']),
                      config['Passwords']['IRC'])
    bot.start()


if __name__ == '__main__':
    print('start')
    main()
