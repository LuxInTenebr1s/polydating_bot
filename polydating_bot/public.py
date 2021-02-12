#!/usr/bin/env python3
"""Module with public chats business logic."""

from telegram.ext import (
    Dispatcher,
#    MessageHandler,
#    Filters,
    CallbackContext,
    CommandHandler
)
from telegram import (
    Update
)

from .data.chatdata import (
    ChatData
)
#from .data.botdata import (
#    BotData
#)

def _start_group(update: Update, context: CallbackContext) -> None:
    try:
        ChatData.from_context(context)
    except KeyError:
        ChatData(update.message.chat).update_context(context)

def add_handlers(dispatcher: Dispatcher) -> None:
    """Add handlers for public conversation."""
    handlers = [
        CommandHandler('start_group', _start_group),
    ]

    for handler in handlers:
        dispatcher.add_handler(handler)
