#!/usr/bin/env python3
"""User data module."""

from __future__ import annotations

import os
import logging

from typing import (
    Dict,
    Optional,
    List,
    Callable,
)

from telegram import (
    Chat,
#    Message,
    ParseMode,
    InputMediaPhoto,
    TelegramError
)
from telegram.ext import (
    CallbackContext,
    Dispatcher,
)

from ..helpers import (
    TG_TRANSLATE
)

from .. import (
    config,
    dating
)
from . import (
    base,
    botdata
)

logger = logging.getLogger(__name__)

class UserData(base.IdData, dating.Form):
    """User data class."""
    _KEY = 'data'
    _MSG_COUNT = 2
    _PHOTO_COUNT = 5

    def __init__(self, chat: Chat):
        super().__init__(chat)

        self._current_question: int = 0

        self._msgs: List[Optional[int]] = [None] * self._MSG_COUNT
        self._back: Optional[Callable] = None
        self._form_ids: Dict[int, List[int]] = dict()

    @property
    def current_question(self) -> int:
        """Current question index."""
        return self._current_question

    @current_question.setter
    def current_question(self, value) -> None:
        bot_data = botdata.BotData.get_instance()
        self._current_question = value % len(bot_data.questions)

    @property
    def back(self):
        """A 'back' function."""
        return self._back

    @back.setter
    def back(self, value) -> None:
        self._back = value

    @classmethod
    def from_context(cls, context: CallbackContext) -> UserData:
        """Get instance of class from CallbackContext data."""
        return context.user_data[cls._KEY]

    def update_context(self, context: CallbackContext) -> None:
        """Update CallbackContext data."""
        context.user_data[self._KEY] = self

    def directory(self) -> str:
        """Get bot directory."""
        dirlist = os.listdir(f'{config.BotConfig.persist_dir}/user')
        path = next(x for x in dirlist if str(x).startswith(str(self.id)))
        return os.path.normpath(f'{config.BotConfig.persist_dir}/user/{path}')

    def clear_messages(self) -> None:
        """Clear bot messages."""
        bot = Dispatcher.get_instance().bot
        for idx, msg in enumerate(self._msgs):
            if not msg:
                continue
            self._msgs[idx] = None
            bot.delete_message(self.id, msg)

    def print_messages(self, *args: Dict) -> None:
        """Print messages. Pass each message argument as keyword dictionary."""
        bot = Dispatcher.get_instance().bot
        for idx, msg in enumerate(self._msgs):
            try:
                kwargs = args[idx]
            except IndexError:
                kwargs = None

            if not kwargs:
                if msg:
                    self._msgs[idx] = None
                    bot.delete_message(self.id, msg)
                continue

            if msg:
                try:
                    var_id = bot.edit_message_text(chat_id=self.id, message_id=msg,
                                                   **kwargs).message_id
                    self._msgs[idx] = var_id
                except TelegramError:
                    pass
            else:
                self._msgs[idx] = bot.send_message(self.id, **kwargs).message_id

    def send_form(self, chat_id: int) -> List[int]:
        """Send form to the specified chat."""
        bot = Dispatcher.get_instance().bot

        if chat_id == botdata.BotData.get_instance().dating_channel:
            for var_id, _ in self._form_ids.items():
                self.delete_form(var_id)
        elif chat_id in self._form_ids:
            self.delete_form(chat_id)

        nick = '*Ник:* ' + self.nick()
        text = self._print_form() + '\n\n' + nick

        msg_ids = []
        msg_ids.append(bot.send_message(chat_id, text,
                                        parse_mode=ParseMode.MARKDOWN_V2).message_id)

        media = list((InputMediaPhoto(file_id) for file_id in self._photo))
        media_list = bot.send_media_group(chat_id, media=media,
                                          reply_to_message_id=msg_ids[-1])
        msg_ids.extend(list(x.message_id for x in media_list))
        self._form_ids[chat_id] = msg_ids

    def delete_form(self, chat_id: int = None):
        """Delete form from dating channel."""
        bot = Dispatcher.get_instance().bot
        bot_data = botdata.BotData.get_instance()

        if not chat_id:
            chat_id = bot_data.dating_channel

        if chat_id and self._form_ids.get(chat_id):
            for var_id in self._form_ids[chat_id]:
                try:
                    bot.delete_message(chat_id, var_id)
                except TelegramError as exc:
                    logger.warning(f'{chat_id}: {var_id}: {exc}')

    def nick(self) -> str:
        """Get formatted nick."""
        bot = Dispatcher.get_instance().bot
        chat = bot.get_chat(self.id)
        if chat.username:
            nick = f'@{chat.username}'.translate(TG_TRANSLATE)
        else:
            name = chat.first_name if chat.first_name else str()
            name += ' ' + chat.last_name if chat.last_name else str()
            name = name.translate(TG_TRANSLATE)
            link = f'tg://user?id={self.id}'.translate(TG_TRANSLATE)
            nick = f'[{name}]({link})'
        return nick
