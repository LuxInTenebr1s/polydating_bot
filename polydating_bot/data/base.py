#!/usr/bin/env python3
"""Bot data base module."""

import logging

from telegram import Chat

logger = logging.getLogger(__name__)

class Data(): # pylint: disable=R0903
    """Bot data base class."""
    _KEY = 'data'

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            logger.warning(f'Trying to evaluate different objects: {other.__class__}')
            return super.__eq__(other)

        logger.debug(f'{vars(self)} and {vars(other)}')
        return vars(self) == vars(other)

class IdData(Data):
    """Bot data base class (with ID)."""
    def __init__(self, chat: Chat):
        if chat.username:
            self._name_id = chat.username
        elif chat.first_name or chat.last_name:
            self._name_id = f'{chat.first_name}_{chat.last_name}'
        elif chat.title:
            self._name_id = chat.title
        else:
            self._name_id = str()

        self._id = chat.id
        super().__init__()

    @property
    def id(self) -> int: # pylint: disable=C0103
        """Chat ID which this data relates to."""
        return self._id

    @property
    def name_id(self) -> str:
        """Name of chat which this data relates to."""
        return self._name_id
