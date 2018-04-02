from multiprocessing import Process
from time import sleep

from globals import config, log
from prismata_bot import PrismataBot

processes = {}


def create_new_bot(channel):
    p = Process(target=start_bot, args=(channel,))
    processes[channel] = p
    p.start()


def terminate_bot(channel):
    process = processes[channel]
    if process.is_alive():
        processes[channel].terminate()
    del processes[channel]


def start_bot(channel):
    bot = PrismataBot('#' + channel,
                      config['Twitch']['nickname'],
                      config['Twitch']['server'],
                      int(config['Twitch']['port']),
                      config['Passwords']['IRC'])
    bot.start()


def main():
    if not config['Passwords']['IRC']:
        log.error("Didn't set up secrets.ini")
        return

    log.debug('1')
    create_new_bot(config['Twitch']['channel'])
    log.debug('1b')

    sleep(10)

    log.debug('2')
    create_new_bot(config['Twitch']['channel2'])
    log.debug('2b')

    sleep(20)
    log.debug('3')
    terminate_bot(config['Twitch']['channel'])
    log.debug('3b')
    sleep(10)
    log.debug('4')
    terminate_bot(config['Twitch']['channel2'])
    log.debug('4b')

    sleep(10)
    log.debug('end')


if __name__ == '__main__':
    log.info('=== Starting BotManager ===')
    main()
