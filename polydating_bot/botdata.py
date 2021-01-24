from typing import List, Dict, Union

from telegram import TelegramObject, Chat, Bot, TelegramError

import helpers

class BotData(TelegramObject):
    def __init__(self, uuid: str):
        self.uuid = uuid
        self.owner: int = None
        self.admin_list: List[int] = []
        self.channel: int = None
        self.pending_forms: List[int] = []
        self.questions: Dict[str, str]

    def check_uuid(self, uuid: str, chat: Chat) -> bool:
        if self.uuid == uuid:
            #TODO: log uuid update
            self.update_owner(chat.id)
            return True
        else:
            #TODO: someone is trying
            return False

    def get_owner(self) -> int:
        return self.owner

    def update_owner(self, id: int) -> None:
        if self.owner:
            pass
            #TODO: send error/notification
        else:
            self.owner = id

    def add_admin(self, id: Union[int, str]) -> None:
        chat_id = helpers.check_chat_id(id)
        if chat_id:
            self.admin_list.append(chat_id)

    def remove_admin(self, id: Union[int, str]) -> None:
        chat_id = helpers.check_chat_id(id)
        if chat_id:
            self.admin_list.remove(chat_id)

    def get_channel(self) -> Dict[int, str]:
        try:
            chat = Bot.get_chat(self.channel)
            return chat
        except TelegramError as exc:
            raise TypeError(f"Channel is not available: {id}") from exc

    def update_channel(self, id: Union[int, str, None]) -> None:
        if not id:
            self.channel = None
        else:
            chat_id = helpers.check_chat_id(id)
            if chat_id:
                self.channel = chat_id

    def add_pending_form(self, id: int) -> None:
        self.pending_forms.append(id)

    def remove_pending_form(self, id: int) -> None:
        self.pending_forms.remove(id)

    def get_questions(self) -> Dict[str, str]:
        return self.questions

    def update_questions(self, questions: Dict[str, str]) -> None:
        self.questions.update(questions)
