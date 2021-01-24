from collections import defaultdict
from typing import List

from telegram import TelegramObject, Chat

class ChatData(TelegramObject):
    def __init__(self, chat: Chat):
        self.id: int = chat.id
        _id_attrs = (self.id, )
