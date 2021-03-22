#!/usr/bin/env python3
# pylint: disable=R0913,C0103
"""Custom persistence module."""

import os
import logging

from collections import (
    defaultdict
)
from copy import (
    deepcopy
)
from typing import (
    Any,
    DefaultDict,
    Dict,
    Optional,
    Tuple
)

import yaml

# Do not import C{Dumper,Loader} as they fail to inherit 'yaml_tag' from YAMLObject
from yaml import (
    Loader,
    Dumper
)
from telegram.ext import (
    BasePersistence
)
from telegram.utils.types import (
    ConversationDict
)

from polydating_bot import (
    PersistenceError
)
from polydating_bot.data import (
    Data,
    DataType
)

logger = logging.getLogger(__name__)

class YamlPersistence(BasePersistence):
    """Custom persistence class."""
    _DATA_FILENAME = "data.yaml"
    _CONV_FILENAME = "conv.yaml"

    def __init__(
        self,
        directory: str,
        store_user_data: bool = True,
        store_chat_data: bool = True,
        store_bot_data: bool = True,
        on_flush: bool = False,
    ):
        super().__init__(
            store_user_data=store_user_data,
            store_chat_data=store_chat_data,
            store_bot_data=store_bot_data,
        )
        self._directory = directory
        self._on_flush = on_flush
        self._user_data: Optional[DefaultDict[int, Dict]] = None
        self._chat_data: Optional[DefaultDict[int, Dict]] = None
        self._bot_data: Optional[Dict] = None
        self._conversations: Optional[Dict[str, Dict[Tuple, Any]]] = None

    @staticmethod
    def _load_file(filename: str, default: Any = None) -> Any:
        try:
            with open(filename, "r") as f:
                data = yaml.load(f, Loader=Loader)
                logger.debug(f'Loaded file successfully: {filename}')
        except OSError:
            logger.warning(f'File \'{filename}\' is missing.')
            data = default
        except yaml.YAMLError as exc:
            mark = getattr(exc, 'problem_mark')
            raise PersistenceError(f'Incorrect YAML: {filename}: {mark}') from exc
        return data

    @staticmethod
    def load_file(filename: str, default: Any = None) -> Any:
        """Load YAML file."""
        return YamlPersistence._load_file(filename, default)

    def _load_data_directory(self, data_type: str) -> Dict:
        data = defaultdict(dict)
        directory = os.path.join(self._directory, data_type)
        if not os.path.exists(directory):
            return data

        logger.debug(f'Files found in \'{directory}\':')
        for path in os.listdir(directory):
            path = os.path.join(directory, path, self._DATA_FILENAME)
            data_item: Data = self._load_file(path)

            data_item.update_dict(data, data_item.id)

        logger.info(f'Directory loaded successfully: {directory}')
        return data

    @staticmethod
    def _dump_file(path: str, data: Any) -> None:
        try:
            os.makedirs(os.path.dirname(path))
        except OSError:
            pass

        try:
            with open(path, 'w') as f:
                yaml.dump(data, f, Dumper=Dumper)
        except OSError as exc:
            raise PersistenceError('Can\'t write file: {path}') from exc


    def _dump_data(self, data: Dict) -> None:
        logger.debug(f'Dumping data: {data}')
        data = Data.from_dict(data)
        path = os.path.join(data.directory(self._directory), self._DATA_FILENAME)
        self._dump_file(path, data)

    def _load_conv(self) -> Dict:
        path = os.path.join(self._directory, DataType.BOT.value, self._CONV_FILENAME)
        data = self._load_file(path)
        return data if data else {}

    def _dump_conv(self) -> None:
        path = os.path.join(self._directory, DataType.BOT.value, self._CONV_FILENAME)
        self._dump_file(path, self._conversations)

    def get_chat_data(self) -> DefaultDict[int, Dict[Any, Any]]:
        if not self._chat_data:
            self._chat_data = self._load_data_directory(DataType.CHAT.value)

        return deepcopy(self._chat_data)

    def update_chat_data(self, chat_id: int, data: Dict) -> None:
        logger.debug(f'Update chat data: {locals()}')
        if self._chat_data.get(chat_id) == data:
            return
        self._chat_data[chat_id] = data

        if not self._on_flush:
            self._dump_data(data)

    def get_user_data(self) -> DefaultDict[int, Dict[Any, Any]]:
        if not self._user_data:
            self._user_data = self._load_data_directory(DataType.USER.value)

        return deepcopy(self._user_data)

    def update_user_data(self, user_id: int, data: Dict) -> None:
        logger.debug(f'Update user data: {locals()}')
        if self._user_data.get(user_id) == data:
            return
        self._user_data[user_id] = data

        if not self._on_flush:
            self._dump_data(data)

    def get_bot_data(self) -> Dict[Any, Any]:
        if not self._bot_data:
            path = os.path.join(self._directory, DataType.BOT.value, self._DATA_FILENAME)
            data = self._load_file(path)
            self._bot_data = {}
            if data:
                data.update_dict(self._bot_data)
        return deepcopy(self._bot_data)

    def update_bot_data(self, data: Dict) -> None:
        logger.debug(f'Update bot data: {locals()}')
        if self._bot_data == data:
            return
        self._bot_data = data

        logger.debug(data)
        if not self._on_flush:
            self._dump_data(data)

    def get_conversations(self, name: str) -> ConversationDict:
        if not self._conversations:
            self._conversations = self._load_conv()

        return deepcopy(self._conversations.get(name, {}))

    def update_conversation(
        self, name: str, key: Tuple[int, ...], new_state: Optional[object]
    ) -> None:
        if not self._conversations:
            self._conversations = {}
        if self._conversations.setdefault(name, {}).get(key) == new_state:
            return
        self._conversations[name][key] = new_state

        if not self._on_flush:
            self._dump_conv()

    def flush(self) -> None:
        for data in self._user_data.values():
            self._dump_data(data)

        for data in self._chat_data.values():
            self._dump_data(data)

        if self._bot_data:
            self._dump_data(self._bot_data)

        if self._conversations:
            self._dump_conv()
