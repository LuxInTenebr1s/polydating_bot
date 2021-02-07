#!/usr/bin/env python3

from __future__ import annotations

from typing import Optional, Dict, List, Tuple
from enum import Enum, auto

class FormStatus(Enum):
    PENDING = 'проверяется админами'
    RETURNED = 'проверка не пройдена'
    IDLE = 'может быть отправлена'
    BLOCKING = 'отправка невозможна'
    PUBLISHED = 'опубликована'

class QuestionFlag(Enum):
    REQUIRED = auto()
    DIGITS = auto()

class _Item():
    def __init__(self, tag: str, value: str):
        if not isinstance(tag, str) and not isinstance(value, str):
            raise TypeError(f'Incorrect type.')
        self.__tag = tag
        self.__value = value

    def __eq__(self, other: _Item):
        if not isinstance(other, _Item):
            raise TypeError(f'Other is of incorrect type.')
        if self.__tag == other.__tag and self.__value == other.__value:
            return True
        return False

    def __str__(self):
        return self.__tag

class _ItemList():
    def __init__(self):
        self.__items: List[_Item] = []

    def __len__(self):
        return len(self.__items)

    def __iter__(self):
        return self.__items.__iter__()

    def __contains__(self, key: object):
        for item in self.__items:
            if item.__tag == str(key):
                return True
        return False

    def __getitem__(self, key):
        for item in self.__items:
            if item.__tag == str(key):
                return item
        raise KeyError(f'Couldn\'t find key: {key}')

class _Question(_Item):
    def __init__(
        self,
        tag: str,
        question: str,
        note: str = str(),
        flags: List[str] = None
    ):
        super().__init__(tag, question)

        self.__note: str = note
        self.__flags: List[QuestionFlag] = []
        for flag in flags:
            self.__flags.append(QuestionFlag[f'{flag}'])

    @property
    def question(self) -> str:
        return self.__value

    @property
    def note(self) -> str:
        return self.__note

    @property
    def flags(self) -> List[QuestionFlag]:
        return self.__flags

_BASE_QUESTIONS = [
    _Question(
        f'name',
        f'Как Вас зовут?',
        f'',
        [QuestionFlag.REQUIRED.name]
    ),
    _Question(
        f'age',
        f'Сколько Вам лет?',
        f'',
        [QuestionFlag.DIGITS.name, QuestionFlag.REQUIRED.name]
    ),
    _Question(
        f'place',
        f'Где Вы живёте?',
        f'Укажите город в формате тэга: напишите название города, заменяя '
        f'дефисы и пробелы на нижнее подчёркивание (\'_\'): например, '
        f'#Нижний_Новгород или #Улан_Удэ. Для городов Москва и Санкт-Петербург '
        f'зарезервированы тэги #Мск и #Спб соответственно.',
        [QuestionFlag.REQUIRED.name]
    )
]

class QuestionList(_ItemList):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, data: List[Dict[str, Dict]]):
        self.__items.append(_BASE_QUESTIONS)

        for kwargs in data:
            question = _Question(**kwargs)
            self.__items.append(question)

    def update_questions(self, data: List[Dict[str, Dict]]):
        self.__init__(data)

    @classmethod
    def get_instance(cls) -> QuestionList:
        return cls.instance

class _Answer(_Item):
    def __init(self, tag: str, answer: str):
        self.__check(answer)
        super().__init__(tag, answer)

    def __check(self, value):
        qlist = QuestionList.get_instance()
        if QuestionFlag.DIGITS in qlist[self.__tag]:
            if not str.isnumeric(value):
                raise ValueError(f'Value must be numeric.')

    @property
    def answer(self) -> str:
        return self.__value

    @answer.setter
    def answer(self, value) -> None:
        self.__check(value)
        self.__value = value

class AnswerList(_ItemList):
    def __setitem__(self, key, item):
        if key in self.__items:
            self.__items[key].answer = item
        else:
            self.__items.append(_Answer(key, item))

class Form():
    def __init__(self, *args, **kwargs):
        self.answers = AnswerList()

        self.__photo: List[str] = []
        self.__sound: Tuple[bool, str] = (False, str())
        self.__nick: str = str()

        self.__status: FormStatus = FormStatus.BLOCKING
        self.__note: str = str()

    def show_status(self) -> str:
        qlist = QuestionList.get_instance()

        qcount = 0
        acount = 0
        for question in qlist:
            if QuestionFlag.REQUIRED in question.flags and not question in self.answers:
                qcount += 1
            if question in self.answers:
                acount += 1

        text = (
            f'Отвечено вопросов: {acount} из {len(qlist)} (ещё {qcount} '
            f'обязательных)\n'
            f'Прикреплено фотографий: {len(self.__photo)}\n'
            f'Выбран саундтрек: '
            f'да' if self.__sound[1] else f'нет', f'\n\n'
            f'Статус анкеты: {self.__status.value}'
        )
        if self.__note and self.__status == FormStatus.RETURNED:
            text += f'\nПримечание админов: {self.__note}'
        return text
