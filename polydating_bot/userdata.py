from __future__ import annotations

import os
import logging
from collections import defaultdict
from typing import Dict, Optional

from telegram import Chat, TelegramObject, Message
from telegram.ext import CallbackContext

import helpers
import config

logger = logging.getLogger(__name__)

class DatingForm():
    NAME = -3
    AGE = -2
    PLACE = -1

    __LOWEST_IDX = NAME
    __questions_count: int = None

    def __init__(self, chat: Chat):
        self.__name: str = str()
        self.__age: int = None
        self.__place: str = str()
        self.__nick: str = helpers.nick_from_chat(chat)

        self.__current_question: Optional[str] = DatingForm.__LOWEST_IDX
        self.answers: Optional[Dict[str, str]] = dict()

    @classmethod
    def set_question_count(cls, value: int):
        cls.__questions_count = value

    @property
    def age(self) -> int:
        return self.__age

    @age.setter
    def age(self, value: int) -> None:
        if not 0 < value < 200:
            raise ValueError(f'Age: incorrect value.')
        self.__age = value

    @property
    def place(self) -> str:
        return self.__place

    @place.setter
    def place(self, value: str) -> None:
        self.__place = str(value)

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        self.__name = str(value)

    @property
    def nick(self) -> str:
        return self.__nick

    @nick.setter
    def nick(self, value) -> None:
        if not isinstance(value, Chat):
            return
        self.__nick = helpers.nick_from_chat(value)

    @property
    def current_question(self) -> int:
        return self.__current_question

    @current_question.setter
    def current_question(self, value: str) -> None:
        if value >= self.__questions_count:
            value = self.__LOWEST_IDX
        elif value < self.__LOWEST_IDX:
            value = self.__questions_count - 1

        self.__current_question = value

class UserData(DatingForm):
    __DATA_KEY = 'data'

    def __init__(self, data: Chat):
        super().__init__(data)
        self.__msg_one: Message = None
        self.__msg_two: Message = None

        self.id: int = data.id

    @property
    def msg_one(self) -> Message:
        return self.__msg_one

    @msg_one.setter
    def msg_one(self, value: Message) -> None:
        if self.__msg_one:
            self.__msg_one.delete()
        self.__msg_one = value

    @msg_one.deleter
    def msg_one(self) -> None:
        return self.__msg_one.delete()

    @property
    def msg_two(self) -> Message:
        return self.__msg_two

    @msg_two.setter
    def msg_two(self, value: Message) -> None:
        if self.__msg_two:
            self.__msg_two.delete()
        self.__msg_two = value

    @msg_two.deleter
    def msg_two(self) -> None:
        return self.__msg_two.delete()

    @staticmethod
    def from_context(context: CallbackContext) -> Optional[UserData]:
        return context.user_data.get('data', None)

    def update_context(self, context: CallbackContext) -> None:
        context.user_data['data'] = self

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
