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
        ChatData(update.message.chat).update_context(context)

    if bot_data.uuid == context.args[0]:
        logger.info('Adding chat to admin chat list.')
        bot_data.admins.append(update.effective_chat.id)

def add_handlers(dispatcher: Dispatcher) -> None:
    """Add handlers for public conversation."""
    handlers = [
        CommandHandler('start', _start),
    ]

    for handler in handlers:
        dispatcher.add_handler(handler, CHAT_GROUP)
