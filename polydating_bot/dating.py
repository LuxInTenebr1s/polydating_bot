#!/usr/bin/env python3
"""Module to describe dating form methods and classes."""

from __future__ import annotations

import logging

from typing import (
    Dict,
    List,
    Tuple,
    Optional
)
from enum import (
    Enum,
    auto
)
from collections.abc import (
    MutableSequence
)
from abc import (
    abstractmethod
)

logger = logging.getLogger(__name__)

class FormStatus(Enum):
    """Enum to describe allowed form statuses."""
    PENDING = 'проверяется админами'
    RETURNED = 'проверка не пройдена'
    IDLE = 'может быть отправлена'
    BLOCKING = 'отправка невозможна'
    PUBLISHED = 'опубликована'

class _QuestionFlag(Enum):
    REQUIRED = auto()
    DIGITS = auto()

class _Item():
    def __init__(self, tag: str, value: str):
        if not isinstance(tag, str) and not isinstance(value, str):
            raise TypeError('Incorrect type.')
        self._tag = tag
        self._value = value

    def __eq__(self, other: _Item):
        logger.debug(f'it happens too: {self} and {other}')
        if not isinstance(other, _Item):
            raise TypeError('Other is of incorrect type.')
        if str(self) == str(other):
            return True
        return False

    def __str__(self):
        return f'{self._tag}: {self._value}'

    @property
    def tag(self) -> str:
        """Tag to select item."""
        return self._tag

class _ItemList(MutableSequence): # pylint: disable=R0901
    def __init__(self):
        self._items: List[_Item] = list()
        super().__init__()

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __contains__(self, key: object):
        for item in self._items:
            logger.debug(f'it happens: {item.tag}')
            if item.tag == str(key):
                return True
        return False

    def __getitem__(self, key):
        if not hasattr(key, 'tag') and str(key).isnumeric():
            return self._items[key]

        for item in self._items:
            if not item.tag == key:
                continue
            return item
        return None

    @abstractmethod
    def __delitem__(self, item):
        pass

    @abstractmethod
    def __setitem__(self, key, item):
        pass

    def insert(self, index, value):
        """Default insert."""
        self._items.insert(index, value)

    def __eq__(self, other):
        logger.debug('KEKEKfdsafadsfa')
        logger.debug(f'item list: {vars(self)} and {vars(other)}')
        super().__eq__(other)

class _Question(_Item):
    def __init__(
        self,
        tag: str,
        question: str,
        note: str = str(),
        flags: List[str] = None
    ):
        super().__init__(tag, question)

        self._note: str = note
        self._flags: List[_QuestionFlag] = []

        if not flags:
            return
        for flag in flags:
            if _QuestionFlag[f'{flag}']:
                self._flags.append(flag)

    @property
    def question(self) -> str:
        """Question."""
        return self._value

    @property
    def note(self) -> str:
        """Question note."""
        return self._note

    @property
    def flags(self) -> List[_QuestionFlag]:
        """Question flags."""
        flags = []
        if not self._flags:
            return flags

        for flag in self._flags:
            if _QuestionFlag[flag]:
                flags.append(_QuestionFlag[flag])
        return flags

_BASE_QUESTIONS = [
    _Question(
        'name',
        'Как Вас зовут?',
        '',
        [_QuestionFlag.REQUIRED.name]
    ),
    _Question(
        'age',
        'Сколько Вам лет?',
        '',
        [_QuestionFlag.DIGITS.name, _QuestionFlag.REQUIRED.name]
    ),
    _Question(
        'place',
        'Где Вы живёте?',
        'Укажите город в формате тэга: напишите название города, заменяя '
        'дефисы и пробелы на нижнее подчёркивание (\'_\'): например, '
        '#Нижний_Новгород или #Улан_Удэ. Для городов Москва и Санкт-Петербург '
        'зарезервированы тэги #Мск и #Спб соответственно.',
        [_QuestionFlag.REQUIRED.name]
    )
]

class QuestionList(_ItemList): # pylint: disable=R0901
    """Questions list. Represents attributes and methods for questions."""
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, data: Optional[List[Dict[str, Dict]]] = None):
        super().__init__()
        self._items += _BASE_QUESTIONS

        if not data:
            return

        for kwargs in data:
            question = _Question(**kwargs)
            self._items.append(question)

    def __setitem__(self, key, item):
        raise SyntaxError('Forbidden for this object.')

    def __delitem__(self, item):
        self._items.__delitem__(item)

    def update_questions(self, data: List[Dict[str, Dict]]):
        """Update questions data."""
        self.__init__(data)

    @classmethod
    def get_instance(cls) -> QuestionList:
        """Get instance of this class (singletone)."""
        return cls.instance

class _Answer(_Item): # pylint: disable=R0903
    def __init__(self, tag: str, answer: str):
        super().__init__(tag, answer)
        self.__check(answer)

    def __check(self, value):
        logger.debug('checking flags.')
        qlist = QuestionList.get_instance()
        if _QuestionFlag.DIGITS in qlist[self._tag].flags:
            if not str.isnumeric(value):
                raise ValueError('Value must be numeric.')

    @property
    def answer(self) -> str:
        """Answer to a question."""
        return self._value

    @answer.setter
    def answer(self, value) -> None:
        self.__check(value)
        self._value = value

class _AnswerList(_ItemList): # pylint: disable=R0901
    """Answers list. Represents attributes and methods for answers."""
    def __setitem__(self, key, item):
        logger.debug(f'{key} and {self._items}')
        if key in self:
            self[key].answer = item
        else:
            logger.debug('Creating new item of answer')
            answer = _Answer(key, item)
            self._items.append(answer)

#    def __getitem__(self, key) -> _Answer:
#        for item in self._items:
#            logger.debug(f'{key} and {item.tag} are compared.')
#            if not item.tag == key:
#                continue
#            return item
#        return None

    def __eq__(self, other):
        logger.debug(f'ans list eq: {vars(self)} and {vars(other)}')
        super().__eq__(other)

    def __delitem__(self, item):
        self._items.__delitem__(item)

class Form():
    """Dating form class."""
    def __init__(self, *args, **kwargs): # pylint: disable=W0613
        logger.debug('KEKEKEKKEKEKEKEKEEKKE')
        self.answers = _AnswerList()

        self._photo: List[str] = []
        self._sound: Tuple[bool, str] = (False, str())
        self._nick: str = str()

        self._status: str = FormStatus.BLOCKING.name
        self._note: str = str()

    def print_form(self) -> None:
        """Prints form to be pulished."""

    def show_status(self) -> str:
        """Returns this form status string."""
        qlist = QuestionList.get_instance()

        qcount = 0
        acount = 0
        for question in qlist:
            if _QuestionFlag.REQUIRED in question.flags and not question in self.answers:
                qcount += 1
            if question in self.answers:
                acount += 1

        text = (
            f'Отвечено вопросов: {acount} из {len(qlist)} (ещё {qcount} '
            f'обязательных)\n'
            f'Прикреплено фотографий: {len(self._photo)}\n'
            f'Выбран саундтрек: '
            f'да' if self._sound[1] else f'нет' f'\n\n'
            f'Статус анкеты: {self._status.value}'
        )
        if self._note and self._status == FormStatus.RETURNED:
            text += f'\nПримечание админов: {self._note}'
        return text
