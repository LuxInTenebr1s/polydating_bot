#!/usr/bin/env python3
"""Module with helper functions."""

import inspect
import logging
from typing import Union, Dict, Optional

from telegram.ext import Dispatcher
from telegram import (
    Bot,
    TelegramError,
)

logger = logging.getLogger(__name__)

def get_chat_id(var_id: Union[str, int]) -> Optional[int]:
    """Check chat ID by ID or username."""
    bot: Bot = Dispatcher.get_instance().bot
    if isinstance(var_id, int) or isinstance(var_id, str) and '@' in var_id:
        try:
            return bot.get_chat(var_id).id
        except TelegramError:
            logger.warning(f'Couldn\'t get chat id: {var_id}')
    return None

def get_property_object(obj: object, attr: str) -> property:
    """Helpers to get properties of the object."""
    assert not attr.startswith('_')

    obj_list = []
    if inspect.isclass(obj):
        obj_list.extend(obj.__class__.mro(obj))
    else:
        obj_list.append(obj).extend(obj.__class__.mro())

    for i in obj_list:
        if attr in i.__dict__:
            return i.__dict__[attr]
    raise AttributeError(obj)

def dict_strip(data: Dict) -> Dict:
    """Helper to strip dictionary from items with 'False' values."""
    keys = []
    for key, val in data.items():
        if not val:
            keys.append(key)
    for key in keys:
        del data[key]
    return data
