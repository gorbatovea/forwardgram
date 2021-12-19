import argparse
import json
import logging
from pathlib import Path

import redis
from redis.client import Redis
from telethon import TelegramClient
from telethon import events
from telethon.tl.custom import Message


# Arguments parsing
def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--cmd', dest='cmd', default='login', help='Command(login|forward)')
    arg_parser.add_argument('--from', dest='forward_from', help='Source')
    arg_parser.add_argument('--to', dest='forward_to', help='Target')
    arg_parser.add_argument('--log-path', dest='log_path', default='logs/', help='Path for logs')
    arg_parser.add_argument('--log-file', dest='log_file', default='forwardgram.log', help='Log file name')
    return arg_parser.parse_args()


args = parse_args()


# Logging
def create_logger(logfile_path, logfile_name):
    Path(logfile_path).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(module)s: %(message)s',
                        filename=logfile_path + logfile_name, filemode='a', level=logging.INFO)
    return logging.getLogger('ForwardGram')


LOGGER = create_logger(args.log_path, args.log_file)

# Configuration
name = 'forwardgram'
config = None

# Client params
forward_from_name = None
forward_to_name = None

# Telegram
client: TelegramClient = None
target_dialog = None
source_dialog_id = None

# Storage
redis_storage: Redis = None
data_expires_in_days = None


async def get_current_session_name():
    me = await client.get_me()
    return [me.first_name, me.username]


def resolve_sender_id(peer_id):
    if hasattr(peer_id, 'channel_id'):
        return peer_id.channel_id
    if hasattr(peer_id, 'chat_id'):
        return peer_id.chat_id
    if hasattr(peer_id, 'user_id'):
        return peer_id.user_id
    LOGGER.error('Error! Cannot resolve sender_id by peer="%s"', peer_id)
    return None


def store_message_mapping(received_message, forwarded_message):
    redis_storage.set(name=received_message.id, value=forwarded_message.id, ex=data_expires_in_days)
    LOGGER.debug('Messages: stored mapping "%d" -> "%d"', received_message.id, forwarded_message.id)


def process_new_message(message):
    if message.reply_to is None:
        return {'message': message, 'reply_to_id': None}

    reply_to_id = redis_storage.get(message.reply_to.reply_to_msg_id)
    if reply_to_id is None:
        message_with_response_header = '[REPLY] \n\n' + message.message
        message.message = message_with_response_header
        message.reply_to = None
        return {'message': message, 'reply_to_id': None}

    return {'message': message, 'reply_to_id': int(reply_to_id)}


async def handle_new_message(event):
    sender_id = resolve_sender_id(event.message.peer_id)

    if sender_id is None:
        LOGGER.warn('Ignoring message "%s"', event.message)
        return

    if sender_id == source_dialog_id:
        new_message_dict = process_new_message(event.message)
        LOGGER.info('Sending message from "%s" to "%s".', forward_from_name, forward_to_name)
        sent_message: Message = await client.send_message(
            target_dialog,
            new_message_dict['message'],
            reply_to=new_message_dict['reply_to_id']
        )
        store_message_mapping(event.message, sent_message)


async def fetch_dialog(name):
    if name is None:
        raise Exception('Error! Argument \'name\' should not be \'None\'.')

    dialogs = await client.get_dialogs()

    # Search be dialog name
    for dialog in dialogs:
        if dialog.name == name:
            return dialog

    # Search be username
    for dialog in dialogs:
        if hasattr(dialog.entity, 'username') \
                and dialog.entity.username == name:
            return dialog

    raise Exception('Error! Target dialog was not found for name="{}"'.format(name))


def start_forwarding(api_id, api_hash):
    global forward_from_name, forward_to_name
    forward_from_name = args.forward_from
    forward_to_name = args.forward_to

    global client
    client = TelegramClient(name, api_id, api_hash)
    client.start()

    current_session = client.loop.run_until_complete(get_current_session_name())
    LOGGER.info('Running as %s(@%s).', current_session[0], current_session[1])

    global target_dialog, source_dialog_id
    target_dialog = client.loop.run_until_complete(fetch_dialog(forward_to_name))
    source_dialog_id = client.loop.run_until_complete(fetch_dialog(forward_from_name)).entity.id

    client.add_event_handler(handle_new_message, events.NewMessage)
    LOGGER.info('Forwarding from "%s"(id=%s) to "%s"(id=%s)', forward_from_name, source_dialog_id, forward_to_name, target_dialog.entity.id)
    client.run_until_disconnected()
    LOGGER.info('Forwarding is done. Exit.')


def login(api_id, api_hash):
    global client
    client = TelegramClient(name, api_id, api_hash)
    client.start()
    current_session = client.loop.run_until_complete(get_current_session_name())
    LOGGER.info('Signed in as %s(@%s).', current_session[0], current_session[1])


def read_configuration(config_path):
    with open(config_path) as json_conf:
        return json.load(json_conf)


def init_redis_storage_client(host, port, password, expiration_time):
    global redis_storage, data_expires_in_days
    redis_storage = redis.Redis(host=host, port=port, password=password, ssl=False)
    data_expires_in_days = expiration_time * 60 * 60 * 24


def main():
    try:
        global config
        config = read_configuration('conf/api_conf.json')

        storage_config = config['storage']
        init_redis_storage_client(
            host=storage_config['host'],
            port=storage_config['port'],
            password=storage_config['password'],
            expiration_time=storage_config['expiration_time']
        )

        if args.cmd == 'login':
            login(api_id=config['api_id'], api_hash=config['api_hash'])
            return 0
        if args.cmd == 'forward':
            start_forwarding(api_id=config['api_id'], api_hash=config['api_hash'])
            return 0
    except Exception as exception:
        LOGGER.error(exception)
        raise exception

    LOGGER.info('Error! Unknown command "%s", available commands: "%s", "%s".', command, login_command, forward_command)


if __name__ == '__main__':
    main()
