#!/usr/bin/env python3
# pylint: disable=R0903
"""Module for common handlers."""

import logging

from telegram.ext import (
    Dispatcher,
    CommandHandler,
    CallbackContext,
)
from telegram import (
    Update,
    TelegramError
)

from polydating_bot import (
    CommandError,
    IncorrectIdError,
    MissingDataError
)
from polydating_bot.data import (
    BotData,
    UserData,
    ChatData,
    FormStatus
)
from polydating_bot.handlers import (
    command_handler,
    HandlerAction,
    HandlerArgumentParser,
    AdminsFilter,
    OwnerFilter,
    COMMON_GROUP,
    new_conv_status,
    REMOVE
)

logger = logging.getLogger(__name__)

class _AdminList(HandlerAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot_data = BotData.from_context(self._context)

        text = [list(), list()]
        for admin in bot_data.admins:
            try:
                if admin > 0:
                    data = UserData.by_id(admin)
                else:
                    data = ChatData.by_id(admin)
            except MissingDataError:
                logger.warning(f'Unknown ID: {admin}')
                bot_data.admins.remove(admin)
                continue

            item = f'{admin} ({data.mention()})'
            if admin > 0:
                text[0].append(item)
            else:
                text[1].append(item)

        text[0] = 'Список админов: ' + ', '.join(text[0])
        text[1] = 'Список админских чатов: ' + ', '.join(text[1])
        bot_data._bot.send_message(self._update.effective_chat.id, '\n'.join(text))

class _AdminAdd(HandlerAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot_data = BotData.from_context(self._context)

        # Try to add admin by reply (seems to be the easiest way to get user ID)
        if self._update.message.reply_to_message:
            reply = self._update.message.reply_to_message
            bot_data.admins.append(reply.from_user.id)
            return

        try:
            var_id = int(values)
        except ValueError:
            try:
                var_id = UserData.by_username(values)
            except MissingDataError as exc:
                raise CommandError('Этот username мне не знаком. :(') from exc
        try:
            bot_data.admins.append(var_id)
        except IncorrectIdError as exc:
            raise CommandError(f'Некорректный ID: {var_id}') from exc

class _AdminRm(HandlerAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot_data = BotData.from_context(self._context)

        for admin in values:
            try:
                admin = int(admin)
                bot_data.admins.remove(admin)
            except ValueError as exc:
                raise CommandError('Несуществующий ID.') from exc

@command_handler
def _admins(update: Update, context: CallbackContext):
    def_args = {'update': update, 'context': context}
    parser = HandlerArgumentParser()
    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser('list', help='list admins')
    list_parser.add_argument('list', nargs=0, action=_AdminList, **def_args)

    add_parser = subparsers.add_parser('add', help='add admin(s) with \'id\'')
    add_parser.add_argument('id', nargs='?', action=_AdminAdd, **def_args)

    rm_parser = subparsers.add_parser('rm', help='remove admin(s) with \'id\'')
    rm_parser.add_argument('id', nargs='*', action=_AdminRm, **def_args)

    parser.parse_args(context.args)

class _PendingList(HandlerAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot_data = BotData.from_context(self._context)
        bot = Dispatcher.get_instance().bot

        text = []
        for var_id in bot_data.pending_forms:
            user_data = UserData.by_id(var_id)
            text.append(f'{var_id} ({user_data.mention()})')
        text = 'Список анкет: ' + ', '.join(text)
        bot.sendMessage(self._update.effective_chat.id, text)

class _PendingShow(HandlerAction):
    def __call__(self, parser, namespace, values, option_string = None):
        user_data = UserData.by_id(int(values[0]))
        chat_data = ChatData.from_context(self._context)

        chat_data.send_form(user_data, callback_data=f'{str(REMOVE)}{user_data.id}')

class _PendingPost(HandlerAction):
    def __call__(self, parser, namespace, values, option_string = None):
        user_data = UserData.by_id(int(values[0]))
        bot_data = BotData.from_context(self._context)
        bot = Dispatcher.get_instance().bot

        if not bot_data.dating_channel:
            raise CommandError('Не указан канал для публикации!')

        logger.debug('Trying to post form..')
        try:
            channel = ChatData.by_id(bot_data.dating_channel)
        except MissingDataError:
            channel = ChatData(bot.getChat(bot_data.dating_channel))
        finally:
            channel.send_form(user_data)

        bot_data.pending_forms.remove(user_data.id)
        user_data.status = FormStatus.PUBLISHED

        new_conv_status(user_data.id)
        logger.info(f'Form was posted: {str(user_data)}')

class _PendingEdit(HandlerAction):
    def __call__(self, parser, namespace, values, option_string = None):
        user_data = UserData.by_id(int(vars(namespace)['id'][0]))

        bot = Dispatcher.get_instance().bot
        bot.send_message(self._update.effective_chat.id, \
                         f"Edit {user_data.mention()}: {' '.join(values)}")

class _PendingReject(HandlerAction):
    def __call__(self, parser, namespace, values, option_string = None):
        user_data = UserData.by_id(int(vars(namespace)['id'][0]))
        bot_data = BotData.from_context(self._context)

        logger.debug('Trying to reject form..')
        user_data.status = FormStatus.RETURNED
        bot_data.pending_forms.remove(user_data.id)
        user_data.note = ' '.join(values)

        new_conv_status(user_data.id)
        logger.info(f'Form was rejected: {str(user_data)}')

@command_handler
def _pending(update: Update, context: CallbackContext):
    def_args = {'update': update, 'context': context}
    parser = HandlerArgumentParser()
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

    reject_parser = subparsers.add_parser('ret', help='reject form if \'id\'')
    reject_parser.add_argument('id', nargs=1)
    reject_parser.add_argument('text', nargs='+', action=_PendingReject, **def_args)

    parser.parse_args(context.args)

class _ChannelShow(HandlerAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot_data = BotData.from_context(self._context)
        bot = Dispatcher.get_instance().bot

        text = 'Канал для публикаций: '

        try:
            if bot_data.dating_channel:
                channel = ChatData.by_id(bot_data.dating_channel)
            else:
                channel = None
        except MissingDataError:
            try:
                channel = ChatData(bot.getChat(bot_data.dating_channel))
            except TelegramError:
                logger.warning(f'Channel seems to be outdated: {bot_data.dating_channel}')
                bot_data.dating_channel = None
                channel = None
        finally:
            if channel:
                text += channel.mention()
            else:
                text += 'отсутствует'
            bot.send_message(self._update.effective_chat.id, text)

class _ChannelSet(HandlerAction):
    def __call__(self, parser, namespace, values, option_string = None):
        bot_data = BotData.from_context(self._context)

        try:
            bot_data.dating_channel = values
        except IncorrectIdError as exc:
            raise CommandError(str(exc)) from exc

@command_handler
def _dating_channel(update: Update, context: CallbackContext):
    def_args = {'update': update, 'context': context}
    parser = HandlerArgumentParser()
    subparsers = parser.add_subparsers()

    list_parser = subparsers.add_parser('show', help='show dating channel')
    list_parser.add_argument('show', nargs=0, action=_ChannelShow, **def_args)

    show_parser = subparsers.add_parser('set', help='set dating channel \'id\'')
    show_parser.add_argument('id', nargs='?', action=_ChannelSet, **def_args)

    parser.parse_args(context.args)

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
        dispatcher.add_handler(handler, COMMON_GROUP)
