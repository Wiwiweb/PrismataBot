from logging.handlers import TimedRotatingFileHandler
import boto3
from botocore.exceptions import NoCredentialsError

from configparser import ConfigParser
import logging

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

# Config secrets
if 'Secrets' not in config:
    config.add_section('Secrets')
if not config['Secrets']['IRC_password']:
    try:
        ssm = boto3.client('ssm', region_name=config['AWS']['region'])
        response = ssm.get_parameters(Names=['IRC_password', 'Twitch_client_id'],
                                      WithDecryption=True)
        config.set('Secrets', 'IRC_password', response['Parameters'][0]['Value'])
        config.set('Secrets', 'Twitch_client_id', response['Parameters'][0]['Value'])
        log.info("Secrets loaded from SSM")
    except NoCredentialsError:
        log.error("Couldn't load secrets!")
        quit()
