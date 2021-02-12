#!/usr/bin/env python3
# pylint: disable=R0903
"""Module for common handlers."""
import logging

from abc import (
    abstractmethod
)

from argparse import (
    ArgumentParser,
    Action
#    ArgumentError,
#    ArgumentTypeError,
#    Namespace
)

from telegram.ext import (
    Dispatcher,
#    Filters,
    CommandHandler,
    CallbackContext,
    MessageFilter
)

from telegram import (
    Update,
    Message
)

from . import (
    helpers
)

from .data.botdata import (
    BotData
)
from .data.userdata import (
    UserData
)
#from .data.chatdata import (
#    ChatData
#)

logger = logging.getLogger(__name__)

def _get_data_by_id(var_id: int) -> UserData:
    user_data = Dispatcher.get_instance().user_data.get(var_id)
    if not user_data:
        raise ValueError('Unknown ID.')
    return user_data['data']

class _CustomAction(Action):
    def __init__(self, *, update, context, **kwargs):
        self._update = update
        self._context = context
        super().__init__(**kwargs)

    @abstractmethod
    def __call__(self, parser, namespace, values, option_string = None):
        pass

class _RedirectArgumentParser(ArgumentParser):
    def error(self, message):
        raise ValueError(f'Error: {message}' + f'\n{self.format_help()}')

class _PendingAction(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot = Dispatcher.get_instance().bot
        bot_data = BotData.get_instance()

        text = []
        for var_id in bot_data.pending_forms:
            user_data = _get_data_by_id(var_id)
            text.append(f'{var_id} ({user_data.name_id})')
        text = 'Список анкет: ' + ', '.join(text)
        bot.send_message(self._update.effective_chat.id, text)

class _ShowAction(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        user_data = _get_data_by_id(int(values[0]))
        bot = Dispatcher.get_instance().bot
        bot.send_message(self._update.effective_chat.id, f'Showing: {user_data.name_id}')

class _PostAction(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        user_data = _get_data_by_id(int(values[0]))
        bot = Dispatcher.get_instance().bot
        bot.send_message(self._update.effective_chat.id, f'Posting: {user_data.name_id}')

class _EditAction(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        user_data = _get_data_by_id(int(vars(namespace)['id'][0]))
        bot = Dispatcher.get_instance().bot
        bot.send_message(self._update.effective_chat.id, f"Edit {user_data.name_id}: {' '.join(values)}")

class AdminsFilter(MessageFilter):
    """Class to filter messages for admins."""
    def filter(self, message: Message):
        bot_data = BotData.get_instance()
        return message.from_user.id in bot_data.admins

class OwnerFilter(MessageFilter):
    """Class to filter messages for owner."""
    def filter(self, message: Message):
        bot_data = BotData.get_instance()
        return message.from_user.id == bot_data.owner

def _parse_admins(update: Update, context: CallbackContext): # pylint: disable=R0912
    bot_data = BotData.get_instance()
    if not context.args: # pylint: disable=R1705
        text = 'Admins list: '
        for var_id in bot_data.admins:
            if var_id in context.dispatcher.user_data:
                text += f"{context.dispatcher.user_data[var_id]['data'].name_id} "
            elif var_id in context.dispatcher.chat_data:
                text += f"{context.dispatcher.chat_data[var_id]['data'].name_id} "
            else:
                logger.error(f'Unknown admin id: {var_id}')
        return text

    elif context.args[0] == 'add':
        if len(context.args) == 1:
            bot_data.admins.append(update.message.chat.id)
            return ''

        for admin in context.args[1: ]:
            try:
                var_id = int(admin)
                bot_data.admins.append(var_id)
            except ValueError:
                var_id = next(x for x, value in context.dispatcher.user_data.items() \
                              if value['data'].name_id == admin)
                bot_data.admins.append(var_id)

    elif context.args[0] == 'rm':
        if len(context.args) == 1:
            logger.warning('Incorrect command use for \'admins\'')
            return 'Specify admins to remove.'

        for admin in context.args[1: ]:
            var_id = 0
            try:
                var_id = int(admin)
            except ValueError:
                var_id = helpers.get_chat_id(admin)
            if var_id in bot_data.admins:
                bot_data.admins.remove(var_id)
            else:
                logger.error(f'Unknown admin id: {var_id}')
    return ''

def _admins(update: Update, context: CallbackContext):
    text = _parse_admins(update, context)
    if text:
        context.bot.send_message(update.message.chat.id, text=text)

def _pending(update: Update, context: CallbackContext):
    def_args = {'update': update, 'context': context}
    parser = _RedirectArgumentParser()
    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser('list', help='list pending form')
    list_parser.add_argument('list', nargs=0, action=_PendingAction, **def_args)

    show_parser = subparsers.add_parser('show', help='show form with \'id\'')
    show_parser.add_argument('id', nargs=1, action=_ShowAction, **def_args)

    post_parser = subparsers.add_parser('post', help='post form with \'id\'')
    post_parser.add_argument('id', nargs=1, action=_PostAction, **def_args)

    edit_parser = subparsers.add_parser('edit', help='edit form with \'id\'')
    edit_parser.add_argument('id', nargs=1)
    edit_parser.add_argument('text', nargs='*', action=_EditAction, **def_args)

    try:
        parser.parse_args(context.args)
    except ValueError as exc:
        context.bot.send_message(update.message.chat.id, text=str(exc))

def add_handlers(dispatcher: Dispatcher) -> None:
    """Add common handlers to dispatcher."""
    handlers = [
        CommandHandler('admins', _admins, filters=OwnerFilter()),
        CommandHandler('pending', _pending, filters=AdminsFilter()),
    ]
    for handler in handlers:
        dispatcher.add_handler(handler)
