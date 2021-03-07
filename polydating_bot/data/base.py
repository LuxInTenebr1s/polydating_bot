#!/usr/bin/env python3
"""Data base class module."""
from __future__ import annotations

import logging
import os

from abc import (
    abstractclassmethod,
    ABCMeta
)
from enum import (
    Enum
)
from typing import (
    Dict,
    Optional
)

from yaml import (
    YAMLObject,
    YAMLObjectMetaclass
)
from telegram import (
    Chat,
    Bot,
    TelegramError,
    utils,
)
from telegram.ext import (
    Dispatcher,
    CallbackContext
)

from polydating_bot import (
    MissingDataError,
    IncorrectIdError
)

logger = logging.getLogger(__name__)

class DataType(Enum):
    """Data type class."""
    USER = 'user'
    CHAT = 'chat'
    BOT = 'bot'

class ABCYamlMeta(YAMLObjectMetaclass, ABCMeta):
    """Combined metaclass of YAMLObjectMetaclass and ABCMeta."""

class Data(YAMLObject, metaclass=ABCYamlMeta): # pylint: disable=R0903
    """Data base class."""
    _KEY: str = 'data'
    _bot: Optional[Bot] = None

    _mapping = {
        'obj': ['_id', '_name_id']
    }

    def __init__(self, chat: Optional[Chat] = None):
        self._id: Optional[int] = None
        self._name_id: Optional[str] = None

        if chat:
            self._id = chat.id
            if chat.username:
                self._name_id = chat.username
            elif chat.title:
                self._name_id = chat.title
            elif chat.full_name:
                self._name_id = chat.full_name

        # Add new data to the bot data list
        data_dict = self._data_by_type()
        self.update_dict(data_dict, self._id)

        super().__init__()

    def __str__(self):
        return f'{self._id}: {self._name_id}'

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            logger.warning(f'Trying to evaluate different objects: {other.__class__}')
            return super.__eq__(other)
        return vars(self) == vars(other)

    @classmethod
    def from_dict(cls, data: Dict, var_id: Optional[int] = None) -> Data:
        """Get data object from dictionary with optional ID."""
        try:
            if var_id:
                return data[var_id][cls._KEY]
            return data[cls._KEY]
        except KeyError as exc:
            str_id = f': {var_id}' if var_id else str()
            logger.debug(f'{data}')
            raise MissingDataError(f'Missing data{str_id}') from exc

    def update_dict(self, data: Dict, var_id: Optional[int] = None) -> None:
        """Update dictionary with data object with optional ID."""
        if var_id:
            data[var_id][self._KEY] = self
        else:
            data[self._KEY] = self

    @classmethod
    def _data_from_context(cls, context: CallbackContext) -> Dict:
        if cls.data_type() == DataType.USER:
            data = context.user_data
        elif cls.data_type() == DataType.CHAT:
            data = context.chat_data
        elif cls.data_type() == DataType.BOT:
            data = context.bot_data
        return data

    @classmethod
    def from_context(cls, context: CallbackContext) -> Data:
        """Get instance of class from CallbackContext data."""
        assert cls.data_type() in DataType
        return cls.from_dict(cls._data_from_context(context))

    def update_context(self, context: CallbackContext) -> None:
        """Update CallbackContext data."""
        assert self.data_type() in DataType
        self.update_dict(self._data_from_context(context))

    @classmethod
    def _data_by_type(cls) -> Dict:
        dispatcher = Dispatcher.get_instance()
        if cls.data_type() == DataType.USER:
            data = dispatcher.user_data
        elif cls.data_type() == DataType.CHAT:
            data = dispatcher.chat_data
        elif cls.data_type() == DataType.BOT:
            data = dispatcher.bot_data
        return data

    @classmethod
    def by_id(cls, var_id: int) -> Data:
        """Get instance of class by ID."""
        assert cls.data_type() in DataType and cls.data_type() != DataType.BOT
        if not var_id:
            raise IncorrectIdError
        return cls.from_dict(cls._data_by_type(), var_id)

    @classmethod
    def by_username(cls, username: str) -> Data:
        """Get instance of class by username."""
        assert cls.data_type() in DataType and cls.data_type() != DataType.BOT
        data = cls._data_by_type()

        data_it = (x for x in data.items() if cls.from_dict(x).name_id == username)
        try:
            return next(data_it)
        except StopIteration as exc:
            raise MissingDataError(f'No data with username {username}') from exc

    @property
    def id(self) -> int: # pylint: disable=C0103
        """Chat ID which this data relates to."""
        return self._id

    def mention(self) -> str:
        """Get Telegram mention by ID."""
        try:
            chat: Chat = self._bot.getChat(self._id)
        except TelegramError as exc:
            raise IncorrectIdError from exc

        if chat.username:
            name = f'@{chat.username}'
        elif chat.type == 'private':
            name = utils.helpers.mention_markdown(self._id, chat.full_name, 2)
        else:
            logger.warning('Trying to do something stupid.')
            name = str()
        return name

    def directory(self, base_dir: str) -> str:
        """Get data object persistent directory."""
        assert self.data_type() in DataType
        root_dir = os.path.join(base_dir, f'{self.data_type().value}')

        if self.data_type() == DataType.BOT:
            path = root_dir
        else:
            path = os.path.join(root_dir, f'{self._id}_{self._name_id}')
        return os.path.normpath(path)

    @classmethod
    def update_bot(cls, bot: Bot) -> None:
        """Bind bot instance for Data class."""
        cls._bot = bot

    @abstractclassmethod
    def data_type(cls) -> DataType:
        """This method must return data type as per DataType values."""

    @abstractclassmethod
    def data_mapping(cls) -> Dict:
        """This method must return data mapping for YAML transformation."""

    @classmethod
    def to_yaml(cls, dumper, data: Data): # pylint: disable=C0116
        mapping = {}

        cls_mapping = dict(cls._mapping)
        cls_mapping.update(cls.data_mapping())

        logger.debug(f'{cls_mapping}')

        for key, val in cls_mapping.items():
            if not isinstance(val, list):
                mapping[key] = getattr(data, val)
            else:
                mapping[key] = []
                for attr in val:
                    mapping[key].append(getattr(data, attr))
        return dumper.represent_mapping(cls.yaml_tag, mapping)

    @classmethod
    def from_yaml(cls, loader, node): # pylint: disable=C0116
        mapping = loader.construct_mapping(node, deep=True)
        data = cls.__new__(cls)

        cls_mapping = dict(cls._mapping)
        cls_mapping.update(cls.data_mapping())

        for key, val in cls_mapping.items():
            if not isinstance(val, list):
                setattr(data, val, mapping[key])
            else:
                for idx, attr in enumerate(val):
                    setattr(data, attr, mapping[key][idx])
        return data
