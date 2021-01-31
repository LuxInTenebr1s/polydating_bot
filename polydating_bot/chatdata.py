from collections import defaultdict
from typing import List

from telegram import TelegramObject, Chat

import helpers

class ChatData(TelegramObject):
    def __init__(self, chat: Chat):
        if chat.title:
            self.name = chat.title
        else:
            self.name = helpers.nick_from_chat(chat)
        self.id: int = chat.id
        self._id_attrs = (self.id, )
