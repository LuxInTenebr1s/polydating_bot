from collections import defaultdict
from typing import Dict

from telegram import Chat, TelegramObject

class DatingForm(TelegramObject):
    def __init__(self, chat: Chat):
        self.questions: Dict[str, str] = defaultdict(str)
        self.name: str
        self.age: int
        self.place: str

        if chat.username:
            self.nick = f'@{chat.username}'
        else:
            self.nick = f'{chat.first_name} {chat.last_name}'

    def get_answer(self, tag: str) -> str:
        return self.questions[tag]

    def update_answer(self, tag: str, answer: str) -> None:
        self.questions[tag] = answer

    def get_age(self) -> int:
        return int(self.age)

    def update_age(self, age: int) -> None:
        self.age = age

    def get_place(self) -> str:
        return self.place

    def update_place(self, place: str) -> None:
        self.place = place

    def get_nick(self) -> str:
        return self.nick

    def update_nick(self, nick: str) -> None:
        self.nice = nick

class UserData(DatingForm):
    def __init__(self, data: Chat):
        super().__init__(data)
        self.id: int = data.id

        _id_attrs: (self.id, )
