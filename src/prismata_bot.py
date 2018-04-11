import json
from difflib import SequenceMatcher
from difflib import get_close_matches

import irc.bot

from globals import config, log

tooltips = json.load(open(config['Files']['unit_tooltips']))
tooltip_key_to_name = {}  # Dictionary of lowercase search terms to actual unit name
for tooltip_dict_name in tooltips:
    tooltip_name_lower = tooltip_dict_name.lower()
    tooltip_key_to_name[tooltip_dict_name] = tooltip_dict_name
    name_parts = tooltip_name_lower.split(' ')
    if len(name_parts) >= 2:
        for name_part in name_parts:
            if name_part not in tooltip_key_to_name:
                tooltip_key_to_name[name_part] = tooltip_dict_name


class PrismataBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port, password):
        log.info('Creating new bot for channel ' + channel)
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, password)], nickname, nickname)
        self.channel = channel

    def on_welcome(self, connection, event):
        connection.join(self.channel)

    def on_join(self, connection, event):
        log.info('New bot joined channel ' + event.target)

    def on_pubmsg(self, connection, event):
        msg = event.arguments[0].split(' ', 1)
        if len(msg) == 2 and len(msg[1]) > 0 and (msg[0].startswith('!unit') or msg[0].startswith('!prismata')):
            self.answer_command(connection, msg[1], event.target)

    def on_disconnect(self, connection, event):
        log.info('Disconnected (channel {}'.format(event.target))
        raise SystemExit()

    def answer_command(self, connection, query, channel):
        log.info('Answering !unit {} in channel {}'.format(query, channel))
        tooltip_key = get_close_matches(query, tooltip_key_to_name.keys(), 1, 0.3)
        if tooltip_key:
            tooltip_key = tooltip_key[0]
            log.debug('Closest match: {} with {}'.format(tooltip_key, SequenceMatcher(None, query, tooltip_key).ratio()))
            tooltip_name = tooltip_key_to_name[tooltip_key]
            connection.privmsg(self.channel, '{}: {}'.format(tooltip_name, tooltips[tooltip_name]))
        else:
            log.debug('Not found')
            connection.privmsg(self.channel, "Couldn't find a unit for {}!".format(query))
