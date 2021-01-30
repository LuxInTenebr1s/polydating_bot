import yaml
try:
    from yaml import CLoader, CDumper as Loader, Dumper
except ImportError:
    from yaml import Loader, Dumper

import os
import logging

from collections import defaultdict
from copy import deepcopy
from typing import Any, DefaultDict, Dict, Optional, Tuple

from telegram.ext import BasePersistence
from telegram.utils.types import ConversationDict

import config
import userdata

USER_DIRECTORY = "user"
CHAT_DIRECTORY = "chat"
CONV_DIRECTORY = "conversation"
BOT_DIRECTORY  = "bot"

DATA_FILENAME = "data.yaml"

logger = logging.getLogger(__name__)

class YamlPersistence(BasePersistence):
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
        self.directory = directory
        self.on_flush = on_flush
        self.user_data: Optional[DefaultDict[int, Dict]] = None
        self.chat_data: Optional[DefaultDict[int, Dict]] = None
        self.bot_data: Optional[Dict] = None
        self.conversations: Optional[Dict[str, Dict[Tuple, Any]]] = None

    def __chat_filename(self, id: int, data: Dict[int, Any]) -> str:
        return os.path.join(self.directory, CHAT_DIRECTORY,
                            f'{id}_{data[id].nick}', f'data.yaml')

    def __user_filename(self, id: int, data: Dict[int, Any]) -> str:
        return os.path.join(self.directory, USER_DIRECTORY,
                            f'{id}_{data[id].nick}', f'data.yaml')

    def __bot_filename(self) -> str:
        return os.path.join(self.directory, BOT_DIRECTORY, DATA_FILENAME)

    @staticmethod
    def __load_file(filename: str) -> Any:
        try:
            with open(filename, "r") as file:
                return yaml.load(file, Loader=Loader)
        except OSError:
            return None
        except yaml.YAMLError as exc:
            mark = getattr(exc, 'problem_mark')
            if mark:
                raise TypeError(f'Incorrect YAML: {filename}: {mark}') from exc
            else:
                raise TypeError(f'YAML loading error: {filename}') from exc
        except Exception as exc:
            raise TypeError(f'Something went wrong loading {filename}') from exc

    @staticmethod
    def __load_directory(directory: str) -> Dict:
        data = defaultdict()
        if not os.path.exists(directory):
            return data

        logger.debug(f'Files found in \'{directory}\':')
        for path in os.listdir(directory):
            id = path.split('_')[0]
            path = os.path.join(directory, path, f'data.yaml')
            data[int(id)] = YamlPersistence.__load_file(path)
            logger.debug(f'\t{path}')

        logger.info(f'Directory loaded successfully: {directory}')
        return data

    @staticmethod
    def __dump_file(filename: str, data: Any) -> None:
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as exc:
                raise TypeError(f"Couldn't make path: {directory}") from exc

        with open(filename, "w") as file:
            yaml.dump(data, file, Dumper=Dumper)

    def get_chat_data(self) -> DefaultDict[int, Dict[Any, Any]]:
        if not self.chat_data:
            pathname = os.path.join(self.directory, CHAT_DIRECTORY)
            self.chat_data = self.__load_directory(pathname)

        return deepcopy(self.chat_data)

    def update_chat_data(self, chat_id: int, data: Dict) -> None:
        if self.chat_data.get(chat_id) == data:
            return
        self.user_data[chat_id] = data

        if not self.on_flush:
            path = self.__chat_filename(chat_id, data)
            self.__dump_file(path, data)

    def get_user_data(self) -> DefaultDict[int, Dict[Any, Any]]:
        if not self.user_data:
            pathname = os.path.join(self.directory, USER_DIRECTORY)
            self.user_data = self.__load_directory(pathname)

        return deepcopy(self.user_data)

    def update_user_data(self, user_id: int, data: Dict) -> None:
        logger.info("update user")
        if self.user_data.get(user_id) == data:
            return
        self.user_data[user_id] = data

        if not self.on_flush:
            path = self.__user_filename(id, data)
            self.__dump_file(path, data)

    def get_bot_data(self) -> Dict[Any, Any]:
        if not self.bot_data:
            data = self.__load_file(self.__bot_filename())
            if not data:
                data = dict()
            self.bot_data = data

        return deepcopy(self.bot_data)

    def update_bot_data(self, data: Dict) -> None:
        if self.bot_data == data:
            return
        self.bot_data = data

        if not self.on_flush:
            self.__dump_file(self.__bot_filename(), data)

    def get_conversations(self, name: str) -> ConversationDict:
        pass

    def update_conversation(
        self, name: str, key: Tuple[int, ...], new_state: Optional[object]
    ) -> None:
        pass

    def flush(self) -> None:
        for _, id in enumerate(self.user_data):
            data = self.user_data
            self.__dump_file(self.__user_filename(id, data), data)

        for _, id in enumerate(self.chat_data):
            data = self.chat_data
            self.__dump_file(self.__chat_filename(id, data), data)

        if self.bot_data:
            data = self.bot_data
            self.__dump_file(self.__bot_filename(), data)

