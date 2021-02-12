#!/usr/bin/env python3
"""Module for chat data."""
from __future__ import annotations

from telegram.ext import (
    CallbackContext
)

from . import (
    base
)

class ChatData(base.IdData):
    """ Represents chat data. """

    @classmethod
    def from_context(cls, context: CallbackContext) -> ChatData:
        """Get data from CallbackContext."""
        return context.chat_data[cls._KEY]

    def update_context(self, context: CallbackContext) -> None:
        """Update CallbackContext data."""
        context.chat_data[self._KEY] = self
