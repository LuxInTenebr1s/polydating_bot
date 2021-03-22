#!/usr/bin/env python3
"""Module with public chats business logic."""

import logging

from telegram.ext import (
    Dispatcher,
    CallbackContext,
    CommandHandler
)
from telegram import (
    Update
)
from telegram.ext import (
    Filters
)

from polydating_bot import (
    MissingDataError
)
from polydating_bot.data import (
    ChatData,
    BotData
)
from polydating_bot.handlers import (
    CHAT_GROUP
)

logger = logging.getLogger(__name__)

def _start(update: Update, context: CallbackContext) -> None:
    bot_data = BotData.from_context(context)
    try:
        ChatData.from_context(context)
    except MissingDataError:
        ChatData(update.effective_chat).update_context(context)

    try:
        if bot_data.uuid == context.args[0]:
            logger.info('Adding chat to admin chat list.')
            bot_data.admins.append(update.effective_chat.id)
        else:
            logger.warning(f'Incorrect deep-link token: {update}')
    except IndexError:
        pass

def add_handlers(dispatcher: Dispatcher) -> None:
    """Add handlers for public conversation."""
    handlers = [
        CommandHandler('start', _start, filters=Filters.chat_type.groups),
    ]

    for handler in handlers:
        dispatcher.add_handler(handler, CHAT_GROUP)
