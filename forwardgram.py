import json
import logging
import sys
from logging import Logger

from telethon import TelegramClient
from telethon import events

# Logging
logging.basicConfig(format='%(asctime)s:%(levelname)s:%(module)s: %(message)s', filename='logs/forwardgram.log', filemode='a', level=logging.INFO)
LOGGER = logging.getLogger('ForwardGram')

# Constants
api_id_key = 'api_id'
api_hash_key = 'api_hash'

# Telegram client conf
api_id = None
api_hash = None
name = 'forwardgram'

# Interface
forward_from_name = None
forward_to_name = None

# Global variables
client: TelegramClient = None
target_dialog = None
source_dialog_id = None


async def get_current_session_name():
    me = await client.get_me()
    return [me.first_name, me.username]


def extract_param(argv, index):
    if argv[index] is None or len(argv[index]) == 0:
        LOGGER.error('Error! Provide argument on %s position.', index)
        exit(1)
    return argv[index]


def extract_params(argv, forward_from_index, forward_to_index):
    if len(argv) < 3:
        LOGGER.error('Error! Provide arguments "forward_from" as a first argument and "forward_to" as a second argument. You have provided %s argument(s)', len(argv) - 1)
        exit(1)
    if argv[forward_from_index] is None or len(argv[forward_from_index]) == 0:
        LOGGER.error('Error! Provide argument "forward_from" as a first argument.')
        exit(1)
    if argv[forward_to_index] is None or len(argv[forward_to_index]) == 0:
        LOGGER.error('Error! Provide argument "forward_to" as a second argument.')
        exit(1)
    return [argv[forward_from_index], argv[forward_to_index]]


def resolve_sender_id(peer_id):
    if hasattr(peer_id, 'channel_id'):
        return peer_id.channel_id
    if hasattr(peer_id, 'chat_id'):
        return peer_id.chat_id
    if hasattr(peer_id, 'user_id'):
        return peer_id.user_id
    LOGGER.error('Error! Cannot resolve sender_id by peer="%s"', peer_id)
    return None


async def handle_new_message(event):
    sender_id = resolve_sender_id(event.message.peer_id)

    if sender_id is None:
        LOGGER.warn('Ignoring message "%s"', event.message)
        return

    if sender_id == source_dialog_id:
        LOGGER.info('Sending message from "%s" to "%s".', forward_from_name, forward_to_name)
        await client.send_message(target_dialog, event.message)


async def fetch_dialog(name):
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


def start_forwarding():
    params = extract_params(sys.argv, 2, 3)
    global forward_from_name, forward_to_name
    forward_from_name = params[0]
    forward_to_name = params[1]

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


def login():
    global client
    client = TelegramClient(name, api_id, api_hash)
    client.start()
    current_session = client.loop.run_until_complete(get_current_session_name())
    LOGGER.info('Signed in as %s(@%s).', current_session[0], current_session[1])


def read_api_configuration():
    with open('conf/api_conf.json') as json_conf:
        conf_dict = json.load(json_conf)
        global api_id, api_hash
        api_id = conf_dict[api_id_key]
        api_hash = conf_dict[api_hash_key]


def main():
    try:
        read_api_configuration()

        login_command = 'login'
        forward_command = 'forward'
        command = extract_param(sys.argv, 1)
        if command == login_command:
            login()
            return 0
        if command == forward_command:
            start_forwarding()
            return 0
    except Exception as exception:
        LOGGER.error(exception)
        raise exception

    LOGGER.info('Error! Unknown command "%s", available commands: "%s", "%s".', command, login_command, forward_command)


if __name__ == '__main__':
    main()
