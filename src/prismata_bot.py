import json
from collections import deque
from datetime import datetime
from difflib import SequenceMatcher, get_close_matches
import random

import irc.bot

from globals import config, log, chat_log

tooltips = json.load(open(config['Files']['unit_tooltips']))
unit_lowercase_to_name = {}  # Dictionary of lowercase unit names to actual unit name
unit_aliases_to_name = {}    # Dictionary of all lowercase aliases terms to actual unit name
for tooltip_dict_name in tooltips:
    tooltip_name_lower = tooltip_dict_name.lower()
    unit_lowercase_to_name[tooltip_name_lower] = tooltip_dict_name
    unit_aliases_to_name[tooltip_name_lower] = tooltip_dict_name
    name_parts = tooltip_name_lower.split(' ')
    if len(name_parts) >= 2:
        for name_part in name_parts:
            if name_part not in unit_aliases_to_name:
                unit_aliases_to_name[name_part] = tooltip_dict_name

custom_tooltips = json.load(open(config['Files']['custom_tooltip_matches']))
unit_aliases_to_name = {**unit_aliases_to_name, **custom_tooltips}  # Merge both dictionaries

prismata_responses = json.load(open(config['Files']['prismata_responses'], encoding='utf8'))


def get_unit_match(query):
    query_lower = query.lower()
    match = None
    if query_lower in unit_lowercase_to_name:
        unit_name = unit_lowercase_to_name[query_lower]
        log.debug('Direct match: {}->{}'.format(query, unit_name))
        return unit_name
    if len(query_lower) >= 4:
        match = get_substring_match(query_lower)
    if match is None:
        match = get_difflib_match(query_lower)
    return match


def get_substring_match(query):
    for key in unit_lowercase_to_name.keys():
        if query in key:
            unit_name = unit_lowercase_to_name[key]
            log.debug('Substring match: {}->{}->{}'.format(query, key, unit_name))
            return unit_name
    return None


def get_difflib_match(query):
    unit_alias = get_close_matches(query, unit_aliases_to_name.keys(), 1, 0.4)
    unit_name = None
    if unit_alias:
        unit_alias = unit_alias[0]
        unit_name = unit_aliases_to_name[unit_alias]
        log.debug('Closest match: {}->{}->{} with {}'
                  .format(query, unit_alias, unit_name,
                          round(SequenceMatcher(None, unit_alias, query).ratio(), 2)))
    return unit_name


class PrismataBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port, password):
        channel = '#' + channel
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, password)], nickname, nickname)
        self.channel = channel
        self.last_chats = deque()
        self.log_chats_in_x = -1

    def on_welcome(self, connection, event):
        log.debug('Connected (channel {})'.format(self.channel))
        connection.cap('REQ', ':twitch.tv/tags')  # Request display-names in messages
        connection.cap('REQ', ':twitch.tv/commands')  # Request ROOMSTATE and CLEARCHAT updates
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

        if self.log_chats_in_x >= 0:
            self.log_chats_in_x -= 1

        message_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.last_chats.append("{} - {}: {}".format(message_time, username, text))
        if len(self.last_chats) > 11:
            self.last_chats.popleft()
        if self.log_chats_in_x == 0:
            for chat_line in self.last_chats:
                chat_log.info(chat_line)

        if text.startswith(('!prismata', '!unit', '@PrismataBot')):
            log.info('Answering "{}" in channel {} from user {}'.format(text, self.channel, username))
            if self.log_chats_in_x > 0:
                for chat_line in self.last_chats:
                    chat_log.info(chat_line)
            else:
                chat_log.info('{}: ================================'.format(self.channel))
            self.log_chats_in_x = 5

        if text_split[0] == '!prismata':
            if len(text_split) == 2:
                self.answer_prismata_command(text_split[1])
        elif text_split[0] == '!unit':
            if len(text_split) == 2:
                self.answer_unit_command(text_split[1])
            else:
                self.chat('You need to type a unit name FailFish')
        elif text_split[0] == '@PrismataBot':
            self.answer_hello_command(username)

    def on_clearchat(self, connection, event):
        if event.arguments[0] == 'prismatabot':
            log.warning("CLEARCHAT: {}".format(event))

    def on_disconnect(self, connection, event):
        log.info('Disconnected (channel {})'.format(self.channel))
        log.debug(event)

    def answer_unit_command(self, query):
        unit_match = get_unit_match(query)
        if unit_match:
            emote = ''
            if 'anime' in query:
                emote = ' TehePelo'
            elif 'goose' in query:
                emote = ' DuckerZ'

            self.chat('{}: {}{}'.format(unit_match, tooltips[unit_match], emote))
        else:
            log.debug('Not found')
            self.chat("Couldn't find a unit for {} NotLikeThis".format(query))

    def answer_prismata_command(self, query):
        tooltip_key = get_close_matches(query, prismata_responses.keys(), 1, 0.6)
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
        faces = ['HeyGuys', 'VoHiYo', 'KonCha', 'MrDestructoid', 'OhMyDog', 'FrankerZ', 'RalpherZ', 'POGGERS']
        self.chat('@{} {}'.format(username, random.choice(faces)))

    def chat(self, message):
        self.connection.privmsg(self.channel, message)
