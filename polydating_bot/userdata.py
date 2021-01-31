from collections import defaultdict
from typing import Dict, Optional

from telegram import Chat, TelegramObject

import helpers

class DatingForm(TelegramObject):
    def __init__(self, chat: Chat):
        self.__name: str
        self.__age: int
        self.__place: str
        self.__nick: str = helpers.nick_from_chat(chat)

        self.answers: Optional[Dict[str, str]] = None

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
        self.__nick = self.__nick_from_chat(value)

class UserData(DatingForm):
    def __init__(self, data: Chat):
        super().__init__(data)
        self.id: int = data.id

        _id_attrs: (self.id, )
