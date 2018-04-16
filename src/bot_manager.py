from multiprocessing import Process
from time import sleep

import requests

from globals import config, log, test_mode
from prismata_bot import PrismataBot

TWITCH_ENDPOINT = 'https://api.twitch.tv/helix/streams?game_id=488455'

processes = {}
bot_lifetimes = {}


def bot_manager_loop():
    sleep_time = int(config['Twitch']['channel_check_sleep'])
    error_sleep_time = int(config['Twitch']['twitch_error_sleep'])

    while True:
        channel_list = get_prismata_streams()

        if channel_list is None:
            sleep(error_sleep_time)
            continue

        reset_bot_lifetimes(channel_list)

        channel_set = set(channel_list)
        existing_bots_set = set(processes.keys())
        new_channels = channel_set - existing_bots_set
        ended_channels = existing_bots_set - channel_set

        if len(new_channels) > 0 or len(ended_channels) > 0:
            log.debug("Existing channels: {} - Existing bots: {}".format(channel_set, existing_bots_set))

        for new_channel in new_channels:
            create_new_bot(new_channel)
        for ended_channel in ended_channels:
            decrement_bot_lifetime(ended_channel)

        sleep(sleep_time)


def get_prismata_streams():
    if test_mode:
        return ['wiwiweb']
    headers = {'Client-ID': config['Secrets']['Twitch_client_id']}
    try:
        r = requests.get(TWITCH_ENDPOINT, headers=headers)
        body = r.json()
        if 'data' not in body or 500 <= r.status_code <= 599:
            log.error("Twitch API {} error : {}".format(r.status_code, body))
            return None
        # Turns "https://static-cdn.jtvnw.net/previews-ttv/live_user_foobar-{width}x{height}.jpg" into "foobar"
        channel_list = [stream['thumbnail_url'][52:-21] for stream in body['data']]
        return channel_list
    except requests.exceptions.RequestException as e:
        log.error("Twitch API request exception: {}".format(e))
        return None


def create_new_bot(channel):
    log.info("Starting new bot for channel: {}".format(channel))
    p = Process(target=start_bot, args=(channel,))
    processes[channel] = p
    p.start()


def start_bot(channel):
    bot = PrismataBot(channel,
                      config['Twitch']['nickname'],
                      config['Twitch']['server'],
                      int(config['Twitch']['port']),
                      config['Secrets']['IRC_password'])
    bot.start()


def reset_bot_lifetimes(channel_list):
    for channel in channel_list:
        if channel in bot_lifetimes:
            log.debug("Bot for channel {} was on lifetime {} but was saved".format(channel, bot_lifetimes[channel]))
            del bot_lifetimes[channel]


def decrement_bot_lifetime(channel):
    if channel not in bot_lifetimes:
        bot_lifetimes[channel] = 5
    else:
        bot_lifetimes[channel] -= 1
    log.debug("Bot for channel {} is on lifetime {}".format(channel, bot_lifetimes[channel]))
    if bot_lifetimes[channel] <= 0:
        terminate_bot(channel)


def terminate_bot(channel):
    log.info("Terminating bot for channel: {}".format(channel))
    process = processes[channel]
    if process.is_alive():
        processes[channel].terminate()
    del processes[channel]
    del bot_lifetimes[channel]


if __name__ == '__main__':
    log.info('=== Starting BotManager ===')
    bot_manager_loop()
