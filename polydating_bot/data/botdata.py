#!/usr/bin/env python3
"""Bot data module."""

from __future__ import annotations

import logging

from uuid import (
    uuid4
)
from typing import (
    Union,
    Optional,
    Tuple,
    Dict
)
from collections.abc import (
    MutableSequence
)

from telegram.ext import (
    Dispatcher
)
from telegram import (
    TelegramError
)
from yaml import (
    YAMLObject
)

from polydating_bot import (
    IncorrectIdError,
)
from polydating_bot.data import (
    ABCYamlMeta,
    Data,
    DataType
)

logger = logging.getLogger(__name__)

class _IdList(MutableSequence, YAMLObject, metaclass=ABCYamlMeta): # pylint: disable=R0901
    yaml_tag = u'!IdList'

    def __init__(self, name: str):
        self._name = name
        self._list = list()

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    def __getitem__(self, idx):
        return self._list.__getitem__(idx)

    def __setitem__(self, idx, value):
        pass

    def __delitem__(self, idx):
        self._list.__delitem__(idx)

    def __str__(self):
        return self._list.__str__()

    def insert(self, index, value):
        """Insert item into list."""

    def append(self, value):
        """Append item to list."""
        bot = Dispatcher.get_instance().bot
        try:
            var_id = bot.getChat(value).id
        except TelegramError as exc:
            raise IncorrectIdError(f'Can\'t get chat: {value}') from exc

        if var_id not in self._list:
            logger.info(f'New id added to \'{self._name}\' list: {var_id}')
            self._list.append(var_id)

    def remove(self, value):
        """Remove item from list."""
        if value in self._list:
            self._list.remove(value)

    @classmethod
    def to_yaml(cls, dumper, data: _IdList):
        mapping = {getattr(data, '_name'): getattr(data, '_list')}
        return dumper.represent_mapping(cls.yaml_tag, mapping)

    @classmethod
    def from_yaml(cls, loader, node):
        mapping = loader.construct_mapping(node)
        data = cls.__new__(cls)
        (name, seq) = mapping.popitem()

        setattr(data, '_name', name)
        setattr(data, '_list', seq)

        return data

class BotData(Data):
    """Bot data class. Data specific to a single bot instance."""
    yaml_tag = u'!BotData'

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            setattr(cls, '_instance', super().__new__(cls, *args, **kwargs))
        return getattr(cls, '_instance')

    def __init__(self):
        self._uuid: str = str(uuid4())
        self._owner: Optional[int] = None
        self._dating_channel: Optional[int] = None
        self._admins: _IdList = _IdList('admins')
        self._pending_forms: _IdList = _IdList('pending_forms')

        super().__init__()

    @classmethod
    def data_type(cls) -> DataType:
        return DataType.BOT

    @classmethod
    def data_mapping(cls) -> Dict:
        return {
            'deeplink': ['_uuid', '_owner'],
            'dating': ['_dating_channel', '_pending_forms', '_admins'],
        }

    @property
    def uuid(self) -> str:
        """Bot UUID string. Used for deep-linking."""
        return self._uuid

    @property
    def owner(self) -> int:
        """Bot owner ID. Grants special permissions to a user with this ID."""
        return self._owner

    @owner.setter
    def owner(self, value: Tuple[str, int]) -> None:
        if self._owner:
            logger.warning('Trying to set new owner! Owner has already been set.')
            return

        if value[0] != self._uuid:
            logger.warning(f'Incorrect UUID! Can\'t set new owner: {value[1]}.')
            return

        try:
            self._owner = self._bot.getChat(value[1]).id
            logger.info(f'Setting new owner: {value[1]}')
        except TelegramError:
            logger.warning(f'Couldn\'t set new owner! Incorrect chat id: {id}')

    @property
    def dating_channel(self) -> Optional[int]:
        """Dating channel ID. Used to publish dating forms."""
        return self._dating_channel

    @dating_channel.setter
    def dating_channel(self, value: Union[int, str, None]) -> None:
        try:
            if not value:
                channel = None
            else:
                channel = self._bot.getChat(value)
        except TelegramError as exc:
            raise IncorrectIdError('Could not find channel.') from exc
        else:
            if channel.type == 'channel':
                self._dating_channel = channel.id
                logger.info(f'Adding new dating channel: {channel.username}')
            else:
                raise IncorrectIdError('Not a channel.')

    @property
    def admins(self) -> _IdList:
        """Admins list."""
        return self._admins

    @property
    def pending_forms(self) -> _IdList:
        """Pending forms list."""
        return self._pending_forms
