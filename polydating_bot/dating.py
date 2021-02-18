#!/usr/bin/env python3
"""Module to describe dating form methods and classes."""

from __future__ import annotations

import logging

from typing import (
    Dict,
    List,
    Tuple,
    Optional,
    Union
)
from enum import (
    Enum,
    auto
)
from collections.abc import (
    MutableSequence
)

from telegram import (
    File
)

from .helpers import (
    TG_TRANSLATE
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

    def extend(self, values):
        """Extends existing list."""
        self._items.extend(values)

    def __delitem__(self, item):
        pass

    def __setitem__(self, key, item):
        pass

    def insert(self, index, value):
        """Default insert."""
        self._items.insert(index, value)

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

_BASE_QUESTIONS = _ItemList()
_BASE_QUESTIONS.extend([
    _Question(
        'name',
        'Как тебя зовут?',
        '',
        [_QuestionFlag.REQUIRED.name]
    ),
    _Question(
        'age',
        'Сколько тебе лет?',
        '',
        [_QuestionFlag.DIGITS.name, _QuestionFlag.REQUIRED.name]
    ),
    _Question(
        'place',
        'Где ты живёшь?',
        'Укажи город в формате тэга: напиши название города, заменяя '
        'дефисы и пробелы на нижнее подчёркивание (\'_\'): например, '
        '#Нижний_Новгород или #Улан_Удэ. Для городов Москва и Санкт-Петербург '
        'зарезервированы тэги #Мск и #Спб соответственно.',
        [_QuestionFlag.REQUIRED.name]
    ),
    _Question(
        'self',
        'Расскажи о себе?',
        'Сообщи любую дополнительную информацию, которую сочтёшь нужной.',
        []
    )
])

class QuestionList(_ItemList): # pylint: disable=R0901
    """Questions list. Represents attributes and methods for questions."""
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, data: Optional[List[Dict[str, Dict]]] = None):
        super().__init__()
        self._items.extend(_BASE_QUESTIONS)

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

    def __delitem__(self, item):
        self._items.__delitem__(item)

class Form():
    """Dating form class."""
    _SOUND_FILE = True

    def __init__(self, *args, **kwargs): # pylint: disable=W0613
        self.answers = _AnswerList()

        self._photo: List[str] = []
        self._sound: Tuple[bool, str] = (False, str())

        self._status: str = FormStatus.BLOCKING.name
        self._note: str = str()

    def _print_header(self) -> str:
        text = (
            f"{self.answers['name'].answer}"
            f"({self.answers['age'].answer}), "
            f"{self.answers['place'].answer}"
        )
        if self.answers['self']:
            text += f"\n\n{self.answers['self'].answer}"
        return text

    def _print_form(self) -> str:
        """Prints form to be pulished."""
        questions = QuestionList.get_instance()
        items = [self._print_header().translate(TG_TRANSLATE)]

        for answer in self.answers:
            # This questions are part of a header
            if answer.tag in _BASE_QUESTIONS:
                continue
            question = questions[answer.tag].question.translate(TG_TRANSLATE)
            item = (f'*{question}*', f'{answer.answer}'.translate(TG_TRANSLATE))
            items.append('\n\n'.join(item))

        if self._sound[1] and not self._sound[0]:
            question = 'Soundtrack: '.translate(TG_TRANSLATE)
            item = (f'*{question}*', f'{self._sound[1]}'.translate(TG_TRANSLATE))
            items.append(''.join(item))

        return '\n\n'.join(items)

    def save_photos(self, photos: List[str]) -> None:
        """Save photos as file_id strings."""
        self._photo = photos

    def save_sound(self, sound: Union[File, str]) -> None:
        """Saves a soundtrack to a local directory (or soundtrack name)."""
        if isinstance(sound, File):
            self._sound = (True, sound.file_id)
        else:
            self._sound = (False, str(sound))

    def show_status(self) -> str:
        """Returns this form status string."""
        qlist = QuestionList.get_instance()

        qcount = 0
        acount = 0
        for question in qlist:
            if _QuestionFlag.REQUIRED in question.flags and not question.tag in self.answers:
                qcount += 1
            if question.tag in self.answers:
                acount += 1

        # Update form status based on number of required questions
        if qcount > 0 or len(self._photo) == 0:
            self._status = FormStatus.BLOCKING.name
        elif self._status == FormStatus.BLOCKING.name:
            self._status = FormStatus.IDLE.name

        text = str().join(
            (
                f'Отвечено вопросов: {acount} из {len(qlist)} (ещё {qcount} '
                f'обязательных)\n'
                f'Прикреплено фотографий: {len(self._photo)}\n'
                f'Выбран саундтрек: ',
                'да' if self._sound[1] else 'нет', '\n\n',
                f'Статус анкеты: {FormStatus[self._status].value}',
            )
        )
        if self._note and self._status == FormStatus.RETURNED.name:
            text += f'\nПримечание админов: {self._note}'
        return text

    @property
    def status(self) -> FormStatus:
        """Form status Enum."""
        return FormStatus[self._status]

    @status.setter
    def status(self, value: FormStatus) -> None:
        self._status = value.name
