import yaml
import os
import logging

from collections import defaultdict
from copy import deepcopy
from typing import Any, DefaultDict, Dict, Optional, Tuple

from telegram.ext import BasePersistence
from telegram.utils.types import ConversationDict

USER_DIRECTORY = "user"
CHAT_DIRECTORY = "chat"
CONV_DIRECTORY = "conversation"

BOT_FILENAME = "bot_data.yaml"

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

    @staticmethod
    def get_filename(id: int, data: Dict) -> str:
        if 'hr_id' in data:
            return f'{id}_{data["hr_id"]}.yaml'
        else:
            return f'{id}_none.yaml'

    @staticmethod
    def load_file(filename: str) -> Any:
        try:
            with open(filename, "r") as file:
                return yaml.load(file)
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
    def load_directory(directory: str) -> Any:
        data = defaultdict(dict)
        if not os.path.exists(directory):
            return data

        for filename in os.listdir(directory):
            id = filename.split('_')[0]
            path = os.path.join(directory, filename)
            data[int(id)] = YamlPersistence.load_file(path)

        logger.info(f"directory loaded: {filename}\n{data}")
        return data

    @staticmethod
    def dump_file(filename: str, data: Any) -> None:
        logger.info(f'dump now: {filename} \n data: {data}')
        directory = os.path.dirname(filename)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError as exc:
                raise TypeError(f"Couldn't make path: {directory}") from exc

        with open(filename, "w") as file:
            yaml.dump(data, file)

    def get_chat_data(self) -> DefaultDict[int, Dict[Any, Any]]:
        if not self.chat_data:
            pathname = os.path.join(self.directory, CHAT_DIRECTORY)
            self.chat_data = self.load_directory(pathname)

        return deepcopy(self.chat_data)

    def update_chat_data(self, chat_id: int, data: Dict) -> None:
        if self.chat_data.get(chat_id) == data:
            return
        self.user_data[chat_id] = data

        if not self.on_flush:
            filename = self.get_filename(chat_id, data)
            path = os.path.join(self.directory, CHAT_DIRECTORY, filename)
            self.dump_file(path, data)

    def get_user_data(self) -> DefaultDict[int, Dict[Any, Any]]:
        logger.info("get user")
        if not self.user_data:
            pathname = os.path.join(self.directory, USER_DIRECTORY)
            self.user_data = self.load_directory(pathname)

        return deepcopy(self.user_data)

    def update_user_data(self, user_id: int, data: Dict) -> None:
        logger.info("update user")
        if self.user_data.get(user_id) == data:
            return
        self.user_data[user_id] = data

        if not self.on_flush:
            filename = self.get_filename(user_id, data)
            path = os.path.join(self.directory, USER_DIRECTORY, filename)
            self.dump_file(path, data)

    def get_bot_data(self) -> Dict[Any, Any]:
        if not self.bot_data:
            filename = os.path.join(self.directory, BOT_FILENAME)
            data = self.load_file(filename)
            if not data:
                data = dict()
            self.bot_data = data

        return deepcopy(self.bot_data)

    def update_bot_data(self, data: Dict) -> None:
        if self.bot_data == data:
            return
        self.bot_data = data

        if not self.on_flush:
            self.dump_file(os.path.join(self.directory, BOT_FILENAME), data)

    def get_conversations(self, name: str) -> ConversationDict:
        return None

    def update_conversation(
        self, name: str, key: Tuple[int, ...], new_state: Optional[object]
    ) -> None:
        return

    def flush(self) -> None:
        for id, data in self.user_data.items():
            filename = self.get_filename(id, data)
            path = os.path.join(self.directory, USER_DIRECTORY, filename)
            self.dump_file(path, data)

        for id, data in self.chat_data.items():
            filename = self.get_filename(id, data)
            path = os.path.join(self.directory, CHAT_DIRECTORY, filename)
            self.dump_file(path, data)

        if self.bot_data:
            path = os.path.join(self.directory, BOT_FILENAME)
            self.dump_file(path, self.bot_data)

