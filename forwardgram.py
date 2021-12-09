import json
import sys

from telethon import TelegramClient
from telethon import events

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
        sys.stderr.write('Error! Provide argument on {} position.'.format(index))
        exit(1)
    return argv[index]


def extract_params(argv, forward_from_index, forward_to_index):
    if len(argv) < 3:
        sys.stderr.write(
            'Error! Provide arguments "forward_from" as a first argument and "forward_to" as a second argument. You have provided {} argument(s)'.format(
                len(argv) - 1))
        exit(1)
    if argv[forward_from_index] is None or len(argv[forward_from_index]) == 0:
        sys.stderr.write('Error! Provide argument "forward_from" as a first argument.')
        exit(1)
    if argv[forward_to_index] is None or len(argv[forward_to_index]) == 0:
        sys.stderr.write('Error! Provide argument "forward_to" as a second argument.')
        exit(1)
    return [argv[forward_from_index], argv[forward_to_index]]


async def handle_new_message(event):
    sender_id = None
    if hasattr(event.message.peer_id, 'channel_id'):
        sender_id = event.message.peer_id.channel_id
    if hasattr(event.message.peer_id, 'chat_id'):
        sender_id = event.message.peer_id.chat_id
    if hasattr(event.message.peer_id, 'user_id'):
        sender_id = event.message.peer_id.user_id

    if sender_id == source_dialog_id:
        print('Sending message from "{}" to "{}".'.format(forward_from_name, forward_to_name))
        await client.send_message(target_dialog, event.message.message)


async def fetch_source_dialog_id(name):
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.name == name:
            return dialog.entity.id


async def fetch_target_dialog(name):
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if dialog.name == name:
            return dialog


def start_forwarding():
    params = extract_params(sys.argv, 2, 3)
    global forward_from_name, forward_to_name
    forward_from_name = params[0]
    forward_to_name = params[1]

    global client
    client = TelegramClient(name, api_id, api_hash)
    client.start()

    current_session = client.loop.run_until_complete(get_current_session_name())
    print('Running as {}(@{}).'.format(current_session[0], current_session[1]))

    global target_dialog, source_dialog_id
    target_dialog = client.loop.run_until_complete(fetch_target_dialog(forward_to_name))
    source_dialog_id = client.loop.run_until_complete(fetch_source_dialog_id(forward_from_name))

    client.add_event_handler(handle_new_message, events.NewMessage)
    print('Forwarding from "{}"(id={}) to "{}"(id={})'.format(forward_from_name, source_dialog_id, forward_to_name,
                                                              target_dialog.entity.id))
    client.run_until_disconnected()


def login():
    global client
    client = TelegramClient(name, api_id, api_hash)
    client.start()
    current_session = client.loop.run_until_complete(get_current_session_name())
    print('Signed in as {}(@{}).'.format(current_session[0], current_session[1]))


def read_api_configuration():
    with open('conf/api_conf.json') as json_conf:
        conf_dict = json.load(json_conf)
        global api_id, api_hash
        api_id = conf_dict[api_id_key]
        api_hash = conf_dict[api_hash_key]


def main():
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

    print('Error! Unknown command "{}", available commands: "{}", "{}".'.format(command, login_command, forward_command))


if __name__ == '__main__':
    main()
