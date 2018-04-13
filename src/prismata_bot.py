import json
from difflib import SequenceMatcher
from difflib import get_close_matches

import irc.bot

from globals import config, log

tooltips = json.load(open(config['Files']['unit_tooltips']))
tooltip_key_to_name = {}  # Dictionary of lowercase search terms to actual unit name
for tooltip_dict_name in tooltips:
    tooltip_name_lower = tooltip_dict_name.lower()
    tooltip_key_to_name[tooltip_name_lower] = tooltip_dict_name
    name_parts = tooltip_name_lower.split(' ')
    if len(name_parts) >= 2:
        for name_part in name_parts:
            if name_part not in tooltip_key_to_name:
                tooltip_key_to_name[name_part] = tooltip_dict_name

custom_tooltips = json.load(open(config['Files']['custom_tooltip_matches']))
tooltip_key_to_name = {**tooltip_key_to_name, **custom_tooltips}  # Merge both dictionaries

prismata_responses = json.load(open(config['Files']['unit_tooltips']))


class PrismataBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port, password):
        channel = '#' + channel
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, password)], nickname, nickname)
        self.channel = channel

    def on_welcome(self, connection, event):
        connection.join(self.channel)

    def on_join(self, connection, event):
        log.debug('New bot joined channel ' + event.target)

    def on_pubmsg(self, connection, event):
        msg = event.arguments[0].split(' ', 1)
        if msg[0].startswith('!prismata'):
            self.answer_unit_command(msg[1], event.target)
        elif msg[0].startswith('!unit'):
            if len(msg) == 2 and len(msg[1]) > 0:
                self.answer_unit_command(msg[1], event.target)
            else:
                self.chat('You need to type a unit name FailFish')

    def on_disconnect(self, connection, event):
        log.info('Disconnected (channel {}'.format(event.target))
        log.debug(event)
        raise SystemExit()

    def answer_unit_command(self, query, channel):
        log.info('Answering !unit {} in channel {}'.format(query, channel))
        tooltip_key = get_close_matches(query, tooltip_key_to_name.keys(), 1, 0.4)
        if tooltip_key:
            tooltip_key = tooltip_key[0]
            tooltip_name = tooltip_key_to_name[tooltip_key]
            log.debug('Closest match: {}->{}->{} with {}'
                      .format(query, tooltip_key, tooltip_name,
                              round(SequenceMatcher(None, query, tooltip_key).ratio(), 2)))
            self.chat('{}: {}'.format(tooltip_name, tooltips[tooltip_name]))
        else:
            log.debug('Not found')
            self.chat("Couldn't find a unit for {} NotLikeThis".format(query))

    def answer_prismata_command(self, query, channel):
        log.info('Answering !prismata {} in channel {}'.format(query, channel))
        if query is None or query == '':
            query = 'prismata'
        tooltip_key = get_close_matches(query, prismata_responses.keys(), 1, 0.5)
        if tooltip_key:
            tooltip_key = tooltip_key[0]
            log.debug('Closest match: {}->{} with {}'
                      .format(query, tooltip_key,
                              round(SequenceMatcher(None, query, tooltip_key).ratio(), 2)))
            self.chat(prismata_responses[tooltip_key])
        else:
            log.debug('Not found')
            query_list = prismata_responses.keys().join(', ')
            self.chat("I don't have anything to say about that FrankerZ I can talk about: {}".format(query_list))

    def chat(self, message):
        self.connection.privmsg(self.channel, message)

