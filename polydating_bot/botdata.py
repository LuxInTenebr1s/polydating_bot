import logging
from typing import List, Dict, Union, Optional, Tuple

from telegram import (
    TelegramObject,
    Bot,
    Chat,
    TelegramError,
)

import config
import helpers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

class BotData():
    __uuid: str = str()
    __owner: Optional[int] = None
    __dating_channel: Optional[int] = None
    __questions: Dict[str, str] = dict()

    admins: helpers.IdList = helpers.IdList('admins')
    pending_forms: helpers.IdList = helpers.IdList('pending_forms')

    def __init__(self, uuid: str):
        self.__uuid = uuid

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
            self.__dating_channel = chat_id

    @dating_channel.deleter
    def dating_channel(self) -> None:
        self.__dating_channel = None

    @property
    def questions(self) -> Dict[str, str]:
        return self.__questions

    @questions.setter
    def questions(self, value: Dict[str, str]) -> None:
        self.__questions = value
