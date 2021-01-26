import inspect
import yaml
import configparser
import logging
from typing import Union

from telegram.ext import Dispatcher
from telegram import (
    Chat,
    Bot,
    TelegramError,
)

logger = logging.getLogger(__name__)

def get_chat(id: Union[id, str]) -> Chat:
    bot = Dispatcher.get_instance()
    if isinstance(id, int) or isinstance(id, str) and '@' in id:
        try:
            return Bot.getChat(bot, id)
        except TelegramError as exc:
            raise TypeError(f"Couldn\'n get chat: {id}") from exc

def check_chat_id(id: Union[id, str]) -> int:
    chat = get_chat(id)
    return chat.id if chat else None

def get_property_object(obj: object, attr: str) -> property:
    obj_list = []
    if inspect.isclass(obj):
        obj_list.extend(obj.__class__.mro(obj))
    else:
        obj_list.append(obj).extend(obj.__class__.mro())

    for obj in obj_list:
        if attr in obj.__dict__:
            return obj.__dict__[attr]
    raise AttributeError(obj)
