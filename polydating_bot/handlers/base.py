#!/usr/bin/env python3
"""Handlers base classes."""

import logging

from argparse import (
    ArgumentParser,
    Action
)
from abc import (
    abstractmethod
)
from decorator import (
    decorator
)

from telegram import (
    Message,
    Update
)
from telegram.ext import (
    MessageFilter,
    Dispatcher,
    CallbackQueryHandler,
    CallbackContext,
    MessageHandler,
    Filters
)

from polydating_bot import (
    CommandError,
    IncorrectIdError,
    MissingDataError
)
from polydating_bot.data import (
    BotData,
    ChatData,
    UserData
)

# Group for base handlers
BASE_GROUP = 0

# Group for private handlers
PRIVATE_GROUP = 10

# Group for chat handlers
CHAT_GROUP = 20

# Group for common handlers
COMMON_GROUP = 30

# Forms actions
(SHOW,
 REMOVE
) = map(chr, range(2))

logger = logging.getLogger(__name__)

@decorator
def command_handler(func, update, context):
    """Command handler decorator."""
    bot = Dispatcher.get_instance().bot
    try:
        func(update, context)
    except CommandError as exc:
        bot.sendMessage(update.effective_chat.id, text=str(exc))

class AdminsFilter(MessageFilter):
    """Class to filter messages for admins."""
    def filter(self, message: Message):
        bot_data = BotData.from_dict(Dispatcher.get_instance().bot_data)
        return message.from_user.id in (bot_data.admins, bot_data.owner)

class OwnerFilter(MessageFilter):
    """Class to filter messages for owner."""
    def filter(self, message: Message):
        bot_data = BotData.from_dict(Dispatcher.get_instance().bot_data)
        return message.from_user.id == bot_data.owner

class HandlerAction(Action):
    """Custom argument parser action."""
    def __init__(self, *, update, context, **kwargs):
        self._update = update
        self._context = context
        super().__init__(**kwargs)

    @abstractmethod
    def __call__(self, parser, namespace, values, option_string = None):
        pass

class HandlerArgumentParser(ArgumentParser):
    """Custom argpument parser."""
    def error(self, message):
        raise CommandError(f'{message}' + f'\n{self.format_help()}')

def _remove(update: Update, context: CallbackContext):
    try:
        var_id = int(update.callback_query.data.lstrip(str(REMOVE)))
    except ValueError:
        return
    chat_data = ChatData.from_context(context)

    try:
        chat_data.delete_form(var_id)
    except (IncorrectIdError, MissingDataError):
        logger.warning(f'Could not remove forms for data: {var_id}')

def _show(update: Update, context: CallbackContext):
    try:
        var_id = int(update.callback_query.data.lstrip(str(SHOW)))
    except ValueError:
        return
    user_data = UserData.by_id(var_id)
    chat_data = ChatData.from_context(context)
    bot_data = BotData.from_context(context)

    if var_id in bot_data.pending_forms:
        chat_data.send_form(user_data, callback_data=f'{str(REMOVE)}{var_id}')
        logger.info(f'Showing data: {str(user_data)}')
    update.callback_query.delete_message()

def _update_chat(update: Update, context: CallbackContext):
    try:
        ChatData.from_context(context).needs_update = True
    except MissingDataError:
        ChatData(update.message.chat).update_context(context)

    try:
        UserData.from_context(context)
    except MissingDataError:
        bot = Dispatcher.get_instance().bot
        chat = bot.getChat(update.message.from_user.id)
        UserData(chat).update_context(context)

def add_handlers(dispatcher: Dispatcher):
    """Add base handlers."""
    handlers = (
        CallbackQueryHandler(_remove, pattern=f'^{REMOVE}.*'),
        CallbackQueryHandler(_show, pattern=f'^{SHOW}.*')
    )
    for handler in handlers:
        dispatcher.add_handler(handler, BASE_GROUP + 1)

    dispatcher.add_handler(MessageHandler(Filters.all, _update_chat), BASE_GROUP)
