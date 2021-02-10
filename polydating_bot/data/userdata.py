#!/usr/bin/env python3
"""User data module."""

from __future__ import annotations

import os
import logging

from typing import (
    Dict,
    Optional,
    List,
    Callable
)

from telegram import (
    Chat,
    Message
)
from telegram.ext import (
    CallbackContext,
    Dispatcher
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

    def __init__(self, chat: Chat):
        super().__init__(chat)

        self._current_question: int = 0

        self._msgs: List[Optional[Message]] = [None] * self._MSG_COUNT
        self._back: Optional[Callable] = None

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
        """Kek."""
        dirlist = os.listdir(f'{config.BotConfig.persist_dir}/user')
        path = next(x for x in dirlist if str(x).startswith(str(self.id)))
        return os.path.normpath(f'{config.BotConfig.persist_dir}/user/{path}')

    def __save_file(self, data, name: str) -> None:
        try:
            dirlist = os.listdir(f'{config.BotConfig.persist_dir}/user')
            path = next(x for x in dirlist if str(x).startswith(str(self.id)))
            logger.debug(f'Saving file: {path}/{name}')
            with open(f'{self.directory()}/{path}/{name}', 'wb') as file:
                file.write(data)
        except OSError as exc:
            raise OSError('Failed to save file: {path}/{name}') from exc

    def save_photo(self, photo, idx: int) -> None:
        """Kek."""
        self.__save_file(photo, f'photo{idx}')

    def clear_messages(self) -> None:
        """Clear bot messages."""
        for idx, _ in enumerate(self._msgs):
            if self._msgs[idx]:
                self._msgs[idx].delete()
                self._msgs[idx] = None

    def print_messages(self, *args: Dict) -> None:
        """Print messages. Pass each message argument as keyword dictionary."""
        for idx, _ in enumerate(self._msgs):
            try:
                kwargs = args[idx]
            except IndexError:
                kwargs = None

            if not kwargs:
                if self._msgs[idx]:
                    self._msgs[idx].delete()
                    self._msgs[idx] = None
                continue

            if not self._msgs[idx]:
                bot = Dispatcher.get_instance().bot
                self._msgs[idx] = bot.send_message(self.id, **kwargs)
            else:
                for key, value in kwargs.items():
                    if vars(self._msgs[idx]).get(key) == value:
                        continue
                    self._msgs[idx] = self._msgs[idx].edit_text(**kwargs)
                    break
