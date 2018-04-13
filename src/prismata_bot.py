import json
from difflib import SequenceMatcher, get_close_matches

import irc.bot
import random

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

prismata_responses = json.load(open(config['Files']['prismata_responses']))


class PrismataBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port, password):
        channel = '#' + channel
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, password)], nickname, nickname)
        self.channel = channel

    def on_welcome(self, connection, event):
        connection.cap('REQ', ':twitch.tv/tags')  # Request display-names in messages
        connection.join(self.channel)

    def on_join(self, connection, event):
        log.debug('New bot joined channel ' + event.target)

    def on_pubmsg(self, connection, event):
        text = event.arguments[0]
        text_split = text.split(' ', 1)

        username = ''
        for tag in event.tags:  # Iterating through to find the key because this gives us a list instead of a dict...
            if tag['key'] == 'display-name':
                username = tag['value']

        if text.startswith(('!prismata', '!unit', '@PrismataBot')):
            log.info('Answering "{}" in channel {} from user {}'.format(text, self.channel, username))

        if text_split[0] == '!prismata':
            if len(text_split) == 1 or text_split[1] == '':
                query = 'prismata'
            else:
                query = text_split[1]
            self.answer_prismata_command(query)
        elif text_split[0] == '!unit':
            if len(text_split) == 2 and len(text_split[1]) > 0:
                self.answer_unit_command(text_split[1])
            else:
                self.chat('You need to type a unit name FailFish')
        elif text_split[0] == '@PrismataBot':
            self.answer_hello_command(username)

    def on_disconnect(self, connection, event):
        log.info('Disconnected (channel {}'.format(event.target))
        log.debug(event)
        raise SystemExit()

    def answer_unit_command(self, query):
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

    def answer_prismata_command(self, query):
        tooltip_key = get_close_matches(query, prismata_responses.keys(), 1, 0.5)
        if tooltip_key:
            tooltip_key = tooltip_key[0]
            log.debug('Closest match: {}->{} with {}'
                      .format(query, tooltip_key,
                              round(SequenceMatcher(None, query, tooltip_key).ratio(), 2)))
            self.chat(prismata_responses[tooltip_key])
        else:
            log.debug('Not found')
            query_list = ', '.join(prismata_responses.keys())
            self.chat("I don't have anything to say about that FrankerZ I can talk about: {}".format(query_list))

    def answer_hello_command(self, username):
        faces = ['HeyGuys', 'VoHiYo', 'KonCha', 'MrDestructoid', 'OhMyDog', 'FrankerZ', 'RalpherZ']
        self.chat('@{} {}'.format(username, random.choice(faces)))

    def chat(self, message):
        self.connection.privmsg(self.channel, message)
