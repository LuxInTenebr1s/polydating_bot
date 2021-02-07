#!/usr/bin/env python3

import logging

from telegram import Chat

logger = logging.getLogger(__name__)

class Data():
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            logger.warning(f'Trying to evaluate different objects: {other.__class__}')
            return super.__eq__(other)

        return vars(self) == vars(other)

class IdData(Data):
    def __init__(self, chat: Chat):
        if chat.username:
            self.__name_id = chat.username
        elif chat.first_name or chat.last_name:
            self.__name_id = f'{chat.first_name}_{chat.last_name}'
        elif chat.title:
            self.__name_id = chat.title
        else:
            self.__name_id = str()

        self.__id = chat.id

    @property
    def id(self) -> int:
        return self.__id

    @property
    def name_id(self) -> str:
        return self.__name_id
