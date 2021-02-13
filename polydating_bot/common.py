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
    Message,
    TelegramError
)

from .dating import (
    FormStatus
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
    if var_id > 0:
        data = Dispatcher.get_instance().user_data.get(var_id)
    else:
        data = Dispatcher.get_instance().chat_data.get(var_id)

    if not data:
        raise ValueError('Неизвестный ID.')
    return data['data']

class AdminsFilter(MessageFilter):
    """Class to filter messages for admins."""
    def filter(self, message: Message):
        bot_data = BotData.get_instance()
        return message.from_user.id in (bot_data.admins, bot_data.owner)

class OwnerFilter(MessageFilter):
    """Class to filter messages for owner."""
    def filter(self, message: Message):
        bot_data = BotData.get_instance()
        return message.from_user.id == bot_data.owner

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

class _AdminList(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot_data = BotData.get_instance()
        bot = Dispatcher.get_instance().bot

        text = [list(), list()]
        for admin in bot_data.admins:
            try:
                data = _get_data_by_id(admin)
            except ValueError:
                logger.warning('Unknown ID')
                continue
            if admin > 0:
                text[0].append(f'{admin} ({data.name_id})')
            else:
                text[1].append(f'{admin} ({data.name_id})')

        text[0] = 'Список админов: ' + ', '.join(text[0])
        text[1] = 'Список админских чатов: ' + ', '.join(text[1])
        bot.send_message(self._update.effective_chat.id, '\n'.join(text))

class _AdminAdd(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot_data = BotData.get_instance()

        if not values:
            bot_data.admins.append(self._update.effective_chat.id)
            return

        try:
            var_id = int(values)
            bot_data.admins.append(var_id)
        except ValueError:
            data_iter = self._context.dispatcher.user_data.items()
            var_id = next(x for x, val in data_iter if val['data'].name_id == values)
            bot_data.admins.append(var_id)

class _AdminRm(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot_data = BotData.get_instance()

        for admin in values:
            try:
                admin = int(admin)
                if admin in bot_data.admins:
                    bot_data.admins.remove(admin)
            except ValueError:
                pass

def _admins(update: Update, context: CallbackContext):
    def_args = {'update': update, 'context': context}
    parser = _RedirectArgumentParser()
    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser('list', help='list admins')
    list_parser.add_argument('list', nargs=0, action=_AdminList, **def_args)

    add_parser = subparsers.add_parser('add', help='add admin(s) with \'id\'')
    add_parser.add_argument('id', nargs='?', action=_AdminAdd, **def_args)

    rm_parser = subparsers.add_parser('rm', help='remove admin(s) with \'id\'')
    rm_parser.add_argument('id', nargs='*', action=_AdminRm, **def_args)

    try:
        parser.parse_args(context.args)
    except ValueError as exc:
        context.bot.send_message(update.message.chat.id, text=str(exc))

class _PendingList(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot = Dispatcher.get_instance().bot
        bot_data = BotData.get_instance()

        text = []
        for var_id in bot_data.pending_forms:
            user_data = _get_data_by_id(var_id)
            text.append(f'{var_id} ({user_data.name_id})')
        text = 'Список анкет: ' + ', '.join(text)
        bot.send_message(self._update.effective_chat.id, text)

class _PendingShow(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        user_data = _get_data_by_id(int(values[0]))
        user_data.send_form(self._update.effective_chat.id)

class _PendingPost(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        user_data = _get_data_by_id(int(values[0]))
        bot_data = BotData.get_instance()
        bot = Dispatcher.get_instance().bot

        if not bot_data.dating_channel:
            raise ValueError('Не указан канал для публикации!')

        chat = bot.get_chat(bot_data.dating_channel)
        user_data.send_form(chat.id)
        user_data.status = FormStatus.PUBLISHED

class _PendingEdit(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        user_data = _get_data_by_id(int(vars(namespace)['id'][0]))
        bot = Dispatcher.get_instance().bot
        bot.send_message(self._update.effective_chat.id, \
                         f"Edit {user_data.name_id}: {' '.join(values)}")

def _pending(update: Update, context: CallbackContext):
    def_args = {'update': update, 'context': context}
    parser = _RedirectArgumentParser()
    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser('list', help='list pending form')
    list_parser.add_argument('list', nargs=0, action=_PendingList, **def_args)

    show_parser = subparsers.add_parser('show', help='show form with \'id\'')
    show_parser.add_argument('id', nargs=1, action=_PendingShow, **def_args)

    post_parser = subparsers.add_parser('post', help='post form with \'id\'')
    post_parser.add_argument('id', nargs=1, action=_PendingPost, **def_args)

    edit_parser = subparsers.add_parser('edit', help='edit form with \'id\'')
    edit_parser.add_argument('id', nargs=1)
    edit_parser.add_argument('text', nargs='*', action=_PendingEdit, **def_args)

    try:
        parser.parse_args(context.args)
    except (ValueError, TelegramError) as exc:
        context.bot.send_message(update.message.chat.id, text=str(exc))

class _ChannelShow(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot_data = BotData.get_instance()
        bot = Dispatcher.get_instance().bot

        text = 'Канал для публикаций: '
        if bot_data.dating_channel:
            text += f'@{bot.get_chat(bot_data.dating_channel).username}'

        bot.send_message(self._update.effective_chat.id, text)

class _ChannelSet(_CustomAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot_data = BotData.get_instance()
        bot = Dispatcher.get_instance().bot

        if not values:
            bot_data.dating_channel = None
            return

        # It's a single item (because of '?')
        chat = bot.get_chat(values)
        if chat.type == 'channel':
            bot_data.dating_channel = chat.id
        else:
            raise ValueError('Не является каналом.')

def _dating_channel(update: Update, context: CallbackContext):
    def_args = {'update': update, 'context': context}
    parser = _RedirectArgumentParser()
    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser('show', help='show dating channel')
    list_parser.add_argument('show', nargs=0, action=_ChannelShow, **def_args)

    show_parser = subparsers.add_parser('set', help='set dating channel \'id\'')
    show_parser.add_argument('id', nargs='?', action=_ChannelSet, **def_args)

    try:
        parser.parse_args(context.args)
    except (ValueError, TelegramError) as exc:
        context.bot.send_message(update.message.chat.id, text=str(exc))

def add_handlers(dispatcher: Dispatcher) -> None:
    """Add common handlers to dispatcher."""
    admins = AdminsFilter()
    owner = OwnerFilter()

    handlers = [
        CommandHandler('admins', _admins, filters=owner),
        CommandHandler('pending', _pending, filters=admins),
        CommandHandler('dating_channel', _dating_channel, filters=admins),
    ]
    for handler in handlers:
        dispatcher.add_handler(handler)
