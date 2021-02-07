#!/usr/bin/env python3

from __future__ import annotations

import os
import logging

from typing import (
    Dict,
    Union,
    Optional,
    Tuple
)

import yaml
try:
    from yaml import CLoader, CDumper as Loader, Dumper
except ImportError:
    from yaml import Loader, Dumper

from telegram.ext import (
    CallbackContext
)
from telegram import (
    TelegramObject,
    Bot,
    Chat,
    TelegramError,
)

from .. import dating
from . import data
import config
import helpers

logger = logging.getLogger(__name__)

class BotData(data.Data):
    __uuid: str = str()
    __owner: Optional[int] = None
    __dating_channel: Optional[int] = None
    __questions: Dict[str, str] = dict()

    admins: helpers.IdList = helpers.IdList('admins')
    pending_forms: helpers.IdList = helpers.IdList('pending_forms')

    def __init__(self, uuid: str):
        self.__uuid = uuid

        try:
            path = os.path.join(config.BotConfig.config_dir, 'dating-form.yaml')
            with open(path) as file:
                self.__questions = yaml.load(file, Loader=Loader)
        except Exception as exc:
            raise ValueError(f'No dating questions found: {exc}') from exc

    @property
    def uuid(self) -> str:
        return self.__uuid

    @property
    def owner(self) -> int:
        return self.__owner

    @owner.setter
    def owner(self, value: Tuple[str, int]) -> None:
        if self.__owner:
            logger.warning(f'Trying to set new owner! Owner has already been set.')
            return

        if value[0] != self.uuid:
            logger.warning(f'Incorrect UUID! Can\'t set new owner: {value[1]}.')
            return

        logger.info(f'helpers')
        id = helpers.get_chat_id(value[1])
        logger.info(f'helpers: {id}')
        if id:
            logger.info(f'Setting new owner: {value[1]}')
            self.__owner = id
        else:
            logger.warning(f'Couldn\'t set new owner! Incorrect chat id: {id}')

    @property
    def dating_channel(self) -> Optional[Dict[int, str]]:
        return self.__dating_channel

    @dating_channel.setter
    def dating_channel(self, value: Union[int, str, None]) -> None:
        id = helpers.get_chat_id(value)
        if id:
            logger.info(f'Adding new dating channel: {id}')
            self.__dating_channel = id

    @dating_channel.deleter
    def dating_channel(self) -> None:
        self.__dating_channel = None

    @property
    def questions(self) -> Dict[str, str]:
        return self.__questions

    @questions.setter
    def questions(self, value: Dict[str, str]) -> None:
        self.__questions = value

    @classmethod
    def from_context(cls, context: CallbackContext) -> BotData:
        return context.bot_data.get('data', None)

    def question_tag_from_idx(self, idx: int) -> str:
        if not 0 <= idx < len(self.questions):
            raise IndexError('Index is out of range')
        return list(self.__questions.items())[idx][0]
