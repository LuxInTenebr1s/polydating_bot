#!/usr/bin/env python3
"""Bot data related module."""

from __future__ import annotations

import os
import logging

from typing import (
    Union,
    Optional,
    Tuple
)
from collections.abc import (
    MutableSequence
)

import yaml
try:
    from yaml import CLoader, CDumper as Loader, Dumper # pylint: disable=W0611
except ImportError:
    from yaml import Loader, Dumper

from telegram.ext import (
    CallbackContext,
    Dispatcher
)
from telegram import (
    ParseMode
)

from .. import (
    dating,
    config,
    helpers
)
from . import (
    base,
    userdata
)

logger = logging.getLogger(__name__)

class _IdList(MutableSequence): # pylint: disable=R0901
    def __init__(self, name: str, *args: Union[int, str]):
        self._name = name
        self._list = list()
        self._list.extend(list(args))

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return len(self._list)

    def __getitem__(self, i):
        return self._list[i]

    def __setitem__(self, i, val):
        pass

    def __delitem__(self, i):
        del self._list[i]

    def __str__(self):
        return str(self._list)

    def insert(self, index, value):
        """Insert item into list."""

    def append(self, value):
        """Append item to the list."""
        var_id = helpers.get_chat_id(value)
        if var_id and var_id not in self._list:
            logger.info(f'New id added to \'{self._name}\' list: {var_id}')
            self._list.append(var_id)

    def remove(self, value):
        """Remove item from the list."""
        if value in self._list:
            self._list.remove(value)

class BotData(base.Data):
    """Bot data class. Data specific to a single bot instance."""
    def __new__(cls, *args, **kwargs): # pylint: disable=W0613
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, uuid: str):
        self._uuid: str = uuid
        self._owner: Optional[int] = None
        self._dating_channel: Optional[int] = None

        self.questions: dating.QuestionList = dating.QuestionList()
        self.admins: _IdList = _IdList('admins')
        self.pending_forms: _IdList = _IdList('pending_forms')

        self.update_questions()

    def update_pending(self, data: userdata.UserData):
        """Add ID to pending list."""
        if data.id in self.pending_forms:
            logger.warning('Trying to add already existing ID.')

        self.pending_forms.append(data.id)
        bot = Dispatcher.get_instance().bot

        for admin in self.admins:
            # Skip all user admins, post to admin chats.
            if admin > 0:
                continue
            text = f'Новая анкета: {data.id} ('.translate(helpers.TG_TRANSLATE)
            text += data.nick()
            text += ')'.translate(helpers.TG_TRANSLATE)
            bot.send_message(admin, text, parse_mode=ParseMode.MARKDOWN_V2)

        data.status = dating.FormStatus.PENDING

    def remove_pending(self, data: userdata.UserData):
        """Remove ID from pending list. In future I should probably add a timer."""
        if data.id not in self.pending_forms:
            logger.warning('Trying to remove missing ID.')

        self.pending_forms.remove(data.id)
        data.status = dating.FormStatus.IDLE

    def update_questions(self):
        """Update questions from configuration directory."""
        try:
            path = os.path.join(config.BotConfig.config_dir, 'dating-form.yaml')
            with open(path) as file:
                self.questions.update_questions(yaml.load(file, Loader=Loader))
        except Exception as exc:
            raise ValueError(f'No dating questions found: {exc}') from exc

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

        var_id = helpers.get_chat_id(value[1])
        if var_id:
            logger.info(f'Setting new owner: {value[1]}')
            self._owner = var_id
        else:
            logger.warning(f'Couldn\'t set new owner! Incorrect chat id: {id}')

    @property
    def dating_channel(self) -> Optional[int]:
        """Dating channel ID. Used to publish dating forms."""
        return self._dating_channel

    @dating_channel.setter
    def dating_channel(self, value: Union[int, str, None]) -> None:
        var_id = helpers.get_chat_id(value)
        if var_id:
            logger.info(f'Adding new dating channel: {id}')
            self._dating_channel = var_id

    @dating_channel.deleter
    def dating_channel(self) -> None:
        self._dating_channel = None

    @classmethod
    def from_context(cls, context: CallbackContext) -> BotData:
        """Get instance from callback context."""
        return context.bot_data.get(cls._KEY, None)

    def update_context(self, context: CallbackContext) -> None:
        """Update callback context with instance."""
        context.bot_data[self._KEY] = self

    @classmethod
    def get_instance(cls) -> BotData:
        """Get data instance."""
        if hasattr(cls, 'instance'):
            return cls.instance
        return None
