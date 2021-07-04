#!/usr/bin/python3
# -*- coding: utf-8 -*-

import configparser
import argparse
import logging
import io
import pprint
import requests
import uuid
import json
import time
import telegram
import telegram.ext


def _setup_logging():
    log_format = '%(asctime)s %(levelname)s@%(pathname)s:%(lineno)d: %(message)s'
    logging.basicConfig(format=log_format,
                        level=logging.INFO)

    root_logger = logging.getLogger()
    # root_logger.setLevel(logging.DEBUG)

    fileHandler = logging.FileHandler("debug.log")
    fileHandler.setFormatter(logging.Formatter(log_format))

    root_logger.addHandler(fileHandler)

    return root_logger


log = _setup_logging()


class Bot:
    config = None
    todoist_users = dict()

    @classmethod
    def config_bot(cls, config):
        cls.config = config
        user_tokens = config['todoist']['users']
        cls.todoist_users = dict(pair.split(':') for pair in user_tokens.split(';'))

    @classmethod
    def create_todoist_task(cls, auth_token, text, due_string="Today"):
        payload = {"content": text,
                   "due_string": due_string}
        headers = {"Content-Type": "application/json",
                   "X-Request-Id": str(uuid.uuid4()),
                   "Authorization": "Bearer {}".format(auth_token)}
        rsp = requests.post("https://api.todoist.com/rest/v1/tasks",
                            data=json.dumps(payload),
                            headers=headers)
        return rsp

    @classmethod
    def receive_message(cls, update: telegram.Update, context: telegram.ext.CallbackContext):
        message = update.message
        user = message.from_user
        username = user.username

        if username in cls.todoist_users:
            task_text = message.text
            user_token = cls.todoist_users[username]
            update.message.reply_text('todoist => "{}"'.format(message.text))
            cls.create_todoist_task(user_token, task_text)
        else:
            update.message.reply_text('Sorry, you are not authorized')
            log.error('Unathorized user: {}'.format(username))


def main(config):
    updater = telegram.ext.Updater(config['telegram']['api_key'], use_context=True)

    # on non command i.e message - bot_echo the message on Telegram
    handler = telegram.ext.MessageHandler(telegram.ext.Filters.text & ~telegram.ext.Filters.command, 
                                          Bot.receive_message)
    updater.dispatcher.add_handler(handler)

    log.debug('Starting bot')
    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':

    config = configparser.ConfigParser()
    config.read('secrets.conf')

    Bot.config_bot(config)

    parser = argparse.ArgumentParser(description='hikbot')
    parser.add_argument('-t', action='store_true')
    args = parser.parse_args()


    if args.t:
        print(Bot.todoist_users)
    else:
        main(config)
