#!/usr/bin/env python3
"""User data module."""

from __future__ import annotations

import logging

from typing import (
    Optional,
    Callable,
    Dict
)

from telegram import (
    Chat
)

from polydating_bot.data import (
    Data,
    DataType,
    Form
)

logger = logging.getLogger(__name__)

class UserData(Data, Form): # pylint: disable=R0902
    """User data class."""
    yaml_tag = u'!UserData'

    def __init__(self, chat: Chat):
        super().__init__(chat)

        self._current_question: int = 0
        self._error: Optional[int] = None
        self._back: Optional[Callable] = None

    @classmethod
    def data_type(cls) -> DataType:
        return DataType.USER

    @classmethod
    def data_mapping(cls) -> Dict:
        return {
            'conv': ['_back', '_current_question'],
            'form': ['_answers', '_status', '_note'],
        }

    @property
    def current_question(self) -> int:
        """Current question index."""
        return self._current_question

    @current_question.setter
    def current_question(self, value) -> None:
        self._current_question = value % len(self.questions)

    @property
    def back(self):
        """A 'back' function."""
        return self._back

    @back.setter
    def back(self, value) -> None:
        self._back = value

    def nick(self) -> str:
        return self.mention()
