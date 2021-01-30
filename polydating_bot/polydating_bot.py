#!/usr/bin/env python
# pylint: disable=W0613, C0116
# type: ignore[union-attr]

import html
import json
import logging
import traceback
from uuid import uuid4

from telegram import Update, ParseMode
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

import helpers
import yamlpersistence
import botdata
from config import BotConfig as config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def debug(update: Update, context: CallbackContext) -> None:
    message = (
        f'<pre>update = {html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>user_data = {html.escape(json.dumps(context.user_data, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>chat_data = {html.escape(json.dumps(context.chat_data, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
    )
    update.message.reply_text(text=message, parse_mode=ParseMode.HTML)

def start(update: Update, context: CallbackContext) -> None:
    logger.info(f'{update.message.text}')
    try:
        data: botdata.BotData = context.bot_data['data']
        data.owner = (context.args[0], update.message.chat.id)
    except:
        pass

def put(update: Update, context: CallbackContext) -> None:
    context.user_data["data"] = update.message.text.partition(' ')[2]

def get(update: Update, context: CallbackContext) -> None:
    message = (
        f'<pre>user_data = {html.escape(json.dumps(context.user_data, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
    )
    update.message.reply_text(text=message, parse_mode=ParseMode.HTML)

def main():
    config.update()
    persistence = yamlpersistence.YamlPersistence(directory=config.persist_dir)

    updater = Updater(config.token, persistence=persistence)
    dispatcher = updater.dispatcher
    logger.info(f'Dispatcher is created.')

    bot_data = dispatcher.bot_data.get('data')
    if not bot_data:
        bot_data = botdata.BotData(str(uuid4()))
        dispatcher.bot_data['data'] = bot_data
        dispatcher.update_persistence()
    logger.info(f'Current bot UUID: {bot_data.uuid}')

    dispatcher.add_handler(CommandHandler('start', start), 1)
    dispatcher.add_handler(CommandHandler('put', put, Filters.chat_type.private))
    dispatcher.add_handler(CommandHandler('get', get, Filters.chat_type.private))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
