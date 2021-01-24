#!/usr/bin/env python
# pylint: disable=W0613, C0116
# type: ignore[union-attr]

import html
import json
import logging
import traceback

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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    message = (
        f'<pre>update = {html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>user_data = {html.escape(json.dumps(context.user_data, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>chat_data = {html.escape(json.dumps(context.chat_data, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
    )
    update.message.reply_text(text=message, parse_mode=ParseMode.HTML)

def put(update: Update, context: CallbackContext) -> None:
    context.user_data["data"] = update.message.text.partition(' ')[2]    

def get(update: Update, context: CallbackContext) -> None:
    message = (
        f'<pre>user_data = {html.escape(json.dumps(context.user_data, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
    )
    update.message.reply_text(text=message, parse_mode=ParseMode.HTML)

def main():
    helpers.parse_arg()

    form = helpers.parse_form()
    for idx,que in enumerate(form['questionnaire']):
        logger.info('%d: %s', idx, que)

    updater = helpers.parse_config('config/default.ini')

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('put', put, Filters.chat_type.private))
    dispatcher.add_handler(CommandHandler('get', get, Filters.chat_type.private))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
