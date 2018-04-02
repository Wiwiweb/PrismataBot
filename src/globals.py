from configparser import ConfigParser
import logging
from logging.handlers import TimedRotatingFileHandler

# Config
CONFIG_FILE = "../cfg/config.ini"
SECRETS_FILE_PRIVATE = "../cfg/secrets.ini"
config = ConfigParser()
config.read([CONFIG_FILE, SECRETS_FILE_PRIVATE])

# Logger
log = logging.getLogger('PrismataBot')
file_handler = TimedRotatingFileHandler(config['Files']['logfile'], 'midnight')
file_handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s - %(message)s'))
log.addHandler(file_handler)
log.setLevel(logging.DEBUG)
