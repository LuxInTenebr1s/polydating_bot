import inspect
import logging
from typing import Union, Dict, Optional
from collections.abc import MutableMapping

from telegram.ext import Dispatcher
from telegram import (
    Chat,
    Bot,
    TelegramError,
)

logger = logging.getLogger(__name__)

class IdList(MutableMapping):
    def __init__(self, name: str, *args: Union[int, str]):
        self.__name = name
        self.__list = list()
        self.__list.extend(list(args))

    def __iter__(self):
        return self.__list

    def __len__(self):
        return len(self.__list)

    def __getitem__(self, i):
        return self.__list[i]

    def __setitem__(self, i, val):
        id = get_chat_id(val)
        if id:
            logger.info(f"New id added to \'{self.__name}'\' list: {id}")
            self.__list[i] = id

    def __delitem__(self, i):
        del self.__list[i]

    def insert(self, i, val):
        id = get_chat_id(val)
        if id:
            logger.info(f"New id added to \'{self.__name}'\' list: {id}")
            self.__list.insert(i, id)

    def append(self, val):
        self.insert(self.__len__(), val)

    def __str__(self):
        return str(self.__list)

def get_chat_id(id: Union[str, int]) -> Optional[int]:
    bot: Bot = Dispatcher.get_instance().bot
    if isinstance(id, int) or isinstance(id, str) and '@' in id:
        try:
            return bot.get_chat(id).id
        except TelegramError:
            logger.warning(f'Couldn\'t get chat id: {id}')
    return None

def get_property_object(obj: object, attr: str) -> property:
    assert not attr.startswith('_')

    obj_list = []
    if inspect.isclass(obj):
        obj_list.extend(obj.__class__.mro(obj))
    else:
        obj_list.append(obj).extend(obj.__class__.mro())

    for obj in obj_list:
        if attr in obj.__dict__:
            return obj.__dict__[attr]
    raise AttributeError(obj)

def dict_strip(data: Dict) -> Dict:
    keys = []
    for key, val in data.items():
        if not val:
           keys.append(key)
    for key in keys:
        del data[key]
    return data

def nick_from_chat(chat: Chat) -> str:
    if chat.username:
        return f'@{chat.username}'
    else:
        return f'{chat.first_name} {chat.last_name}'


