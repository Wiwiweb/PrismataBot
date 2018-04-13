from multiprocessing import Process
from time import sleep

import requests

from globals import config, log
from prismata_bot import PrismataBot

TWITCH_ENDPOINT = 'https://api.twitch.tv/kraken/streams?game=Prismata&client_id={}'\
    .format(config['Secrets']['Twitch_client_id'])

processes = {}


def bot_manager_loop():
    sleep_time = int(config['Twitch']['channel_check_sleep'])
    while True:
        channel_set = set(get_prismata_streams())
        existing_bots_set = set(processes.keys())
        new_channels = channel_set - existing_bots_set
        ended_channels = existing_bots_set - channel_set

        for new_channel in new_channels:
            create_new_bot(new_channel)
        for ended_channel in ended_channels:
            terminate_bot(ended_channel)

        sleep(sleep_time)


def get_prismata_streams():
    body = requests.get(TWITCH_ENDPOINT).json()
    if 'stream' not in body:
        log.error("Twitch API error : {}".format(body))
    channel_list = [stream['channel']['name'] for stream in body['streams']]
    return channel_list


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


def terminate_bot(channel):
    log.info("Terminating bot for channel: {}".format(channel))
    process = processes[channel]
    if process.is_alive():
        processes[channel].terminate()
    del processes[channel]


if __name__ == '__main__':
    log.info('=== Starting BotManager ===')
    bot_manager_loop()
