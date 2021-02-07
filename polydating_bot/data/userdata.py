#!/usr/bin/env python3

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

import config
import dating
import data

logger = logging.getLogger(__name__)

class UserData(data.IdData, dating.Form):
    _KEY = 'data'
    _MSG_COUNT = 2

    def __init__(self, chat: Chat):
        super().__init__(chat)

        self.__id: int = chat.id

        self.__msgs: List[Optional[Message]] = [None] * self._MSG_COUNT
        self.__back: Optional[Callable] = None

    @property
    def id(self) -> int:
        return self.__id

    @property
    def back(self):
        return self.__back

    @back.setter
    def back(self, value) -> None:
        self.__back = value

    @classmethod
    def from_context(cls, context: CallbackContext) -> UserData:
        return context.user_data[cls._KEY]

    def update_context(self, context: CallbackContext) -> None:
        context.user_data[self._KEY] = self

    def directory(self) -> str:
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
        except:
            raise OSError('Failed to save file: {path}/{name}')

    def save_photo(self, photo, idx: int) -> None:
        self.__save_file(photo, f'photo{idx}')

    def clear_messages(self) -> None:
        for idx, _ in enumerate(self.__msgs):
            if self.__msgs[idx]:
                self.__msgs[idx].delete()
                self.__msgs[idx] = None

    def print_messages(self, *args: Dict) -> None:
        for idx, _ in enumerate(self.__msgs):
            try:
                kwargs = args[idx]
            except:
                kwargs = None

            if not kwargs:
                if self.__msgs[idx]:
                    self.__msgs[idx].delete()
                    self.__msgs[idx] = None
                continue

            if not self.__msgs[idx]:
                bot = Dispatcher.get_instance().bot
                self.__msgs[idx] = bot.send_message(self.id, **kwargs)
            else:
                self.__msgs[idx].edit_text(**kwargs)
