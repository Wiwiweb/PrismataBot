import logging
import os
import sys
from traceback import format_tb

from configparser import ConfigParser
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler

# Test mode
if len(sys.argv) > 1 and '--test' in sys.argv:
    print("=== TEST MODE ===")
    test_mode = True
else:
    test_mode = False

# Config
CONFIG_FILE = "../cfg/config.ini"
SECRETS_FILE_PRIVATE = "../cfg/secrets.ini"
config = ConfigParser()
config.read([CONFIG_FILE, SECRETS_FILE_PRIVATE])

# Logger
log = logging.getLogger('PrismataBot')
log.setLevel(logging.DEBUG)
log_format = '%(asctime)s: %(levelname)s - %(message)s'
handler = StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(log_format))
log.addHandler(handler)

chat_log = logging.getLogger('PrismataBot_chat')
chat_log.setLevel(logging.INFO)
log_format = '%(message)s'
handler = TimedRotatingFileHandler(config['Files']['logfile_chat'], 'midnight')
handler.setFormatter(logging.Formatter(log_format))
chat_log.addHandler(handler)

# Exception logging
def log_uncaught_exceptions(ex_cls, ex, tb):
    log.critical(''.join(format_tb(tb)))
    log.critical('{0}: {1}'.format(ex_cls, ex))

sys.excepthook = log_uncaught_exceptions

# Config secrets
if 'Secrets' not in config:
    config.add_section('Secrets')
if not config['Secrets']['IRC_password']:
    try:
        config.set('Secrets', 'IRC_password', os.environ['IRC_PASSWORD'])
        config.set('Secrets', 'Twitch_client_id', os.environ['TWITCH_CLIENT_ID'])
        log.info("Secrets loaded from env vars")
    except KeyError:
        log.error("Couldn't load secrets!")
        raise SystemExit()
