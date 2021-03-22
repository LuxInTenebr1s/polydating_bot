#!/usr/bin/env python3
"""Dating form module."""

from __future__ import annotations

import logging

from typing import (
    List,
    Union,
    Any,
    Tuple
)
from enum import (
    Enum,
    auto
)
from abc import (
    abstractmethod
)
from collections.abc import (
    MutableSequence
)

from telegram import (
    utils,
    Message,
    constants
)
from yaml import (
    YAMLObject
)

from polydating_bot import (
    AnswerError,
    MissingDataError
)
from polydating_bot.data import (
    ABCYamlMeta
)

logger = logging.getLogger(__name__)

class FormStatus(Enum):
    """Allowed form statuses."""
    PENDING = 'проверяется админами'
    RETURNED = 'проверка не пройдена'
    IDLE = 'может быть отправлена'
    BLOCKING = 'отправка невозможна'
    PUBLISHED = 'опубликована'

class QuestionType(Enum):
    """Allowed question types."""
    TEXT = auto()
    DIGITS = auto()
    AUDIO = auto()
    PHOTO = auto()

class _Item(YAMLObject):
    def __init__(self, tag: str, value: Any):
        self._tag: str = tag
        self._value: Any = value

    def __eq__(self, other: _Item):
        if not isinstance(other, _Item):
            logger.warning('Other is of incorrect type.')
            return False

        if self._tag == other.tag and self._value == other.value:
            return True
        return False

    def __str__(self):
        return f'{self._tag}: {self._value}'

    @property
    def tag(self) -> str:
        """Tag to select item."""
        return self._tag

    @property
    def value(self) -> Any:
        """Value of item."""
        return self._value

class _ItemList(YAMLObject, MutableSequence, metaclass=ABCYamlMeta): # pylint: disable=R0901
    def __init__(self, item_list: Union[List[_Item], _ItemList] = None):
        self._items: List[_Item] = list()
        if item_list:
            self.extend(item_list)
        super().__init__()

    def __len__(self):
        return self._items.__len__()

    def __iter__(self):
        return self._items.__iter__()

    def __contains__(self, key: object):
        try:
            if isinstance(key, int):
                return False
            self.__getitem__(key)
            return True
        except MissingDataError:
            return False

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._items[key]

        if isinstance(key, _Item):
            tag = key.tag
        else:
            tag = str(key)

        for item in self._items:
            if item.tag != tag:
                continue
            return item
        raise MissingDataError

    def __delitem__(self, item):
        pass

    def __setitem__(self, key, item):
        pass

    def extend(self, values: Union[_ItemList, List[_Item]]):
        """Extends existing list."""
        for item in values:
            assert isinstance(item, _Item)
        self._items.extend(values)

    def append(self, value: _Item):
        """Append item to existing list."""
        assert isinstance(value, _Item)
        self._items.append(value)

    def insert(self, index, value: _Item):
        """Default insert."""
        assert isinstance(value, _Item)
        self._items.insert(index, value)

    @classmethod
    def to_yaml(cls, dumper, data: _ItemList):
        return dumper.represent_sequence(cls.yaml_tag, data)

    @classmethod
    def from_yaml(cls, loader, node):
        seq = loader.construct_sequence(node)
        return cls(seq)

class _Question(_Item):
    yaml_tag = u'!Question'

    def __init__(
        self,
        tag: str,
        value: str,
        note: str = str(),
        question_type: str = QuestionType.TEXT.name,
        required: bool = False
    ): # pylint: disable=R0913
        super().__init__(tag, value)

        self._note: str = note
        self._required = required

        question_type = question_type.upper()
        try:
            QuestionType[question_type]
        except KeyError as exc:
            raise TypeError('Incorrect question type.') from exc
        self._question_type = question_type

    @classmethod
    def to_yaml(cls, dumper, data: _Question):
        req_mark = '*' if data.required else ''
        question = f'{data.tag}: {req_mark}{data.value}'

        seq = [question, data.note, data.question_type.name.lower()]
        return dumper.represent_sequence(cls.yaml_tag, seq)
    @classmethod
    def from_yaml(cls, loader, node):
        seq = loader.construct_sequence(node)
        (tag, _, question) = seq[0].partition(':')

        question = question.lstrip()
        required = question.startswith('*')

        return cls(tag, question.lstrip('*'), seq[1], seq[2], required)

    @property
    def note(self) -> str:
        """Question note."""
        return self._note

    @property
    def question_type(self) -> QuestionType:
        """Question type of QuestionType Enum type."""
        return QuestionType[self._question_type]

    @property
    def required(self) -> bool:
        """Required question flag."""
        return self._required

_BASE_QUESTIONS = _ItemList([
    _Question(
        'name',
        'Как тебя зовут?',
        '',
        'text',
        True
    ),
    _Question(
        'age',
        'Сколько тебе лет?',
        '',
        'digits',
        True
    ),
    _Question(
        'place',
        'Где ты живёшь?',
        'Укажи город в формате тэга: напиши название города, заменяя '
        'дефисы и пробелы на нижнее подчёркивание (\'_\'): например, '
        '#Нижний_Новгород или #Улан_Удэ. Для городов Москва и Санкт-Петербург '
        'зарезервированы тэги #Мск и #Спб соответственно.',
        'text',
        True
    ),
    _Question(
        'self',
        'Расскажи о себе?',
        'Сообщи любую дополнительную информацию, которую сочтёшь нужной.',
        'text',
        False
    )
])

_FINAL_QUESTIONS = _ItemList([
    _Question(
        'photo',
        'Пришли до пяти (5) своих фотографий одним сообщением (альбом).',
        '',
        'photo',
        True
    ),
    _Question(
        'soundtrack',
        'Пришли одно (1) аудио или название трека.',
        'Название будет записано в анкете как есть. Можно переслать сообщение '
        'с прикреплённым аудио от другого бота.',
        'audio',
        False
    ),
])

class _QuestionList(_ItemList): # pylint: disable=R0901
    """Questions list. Represents attributes and methods for questions."""
    yaml_tag = u'!Questions'

    def __init__(self, questions: List[_Question] = None):
        super().__init__()
        self._items.extend(_BASE_QUESTIONS)
        if questions:
            self._items.extend(questions)
        self._items.extend(_FINAL_QUESTIONS)

class _Answer(_Item): # pylint: disable=R0903
    yaml_tag = u'!Answer'

    def __init__(self, tag: str, answer: str):
        super().__init__(tag, answer)

    @_Item.value.setter
    def value(self, value: Any)-> None:
        self._value = value

    @classmethod
    def to_yaml(cls, dumper, data: _Answer):
        return dumper.represent_mapping(cls.yaml_tag, {data.tag: data.value})

    @classmethod
    def from_yaml(cls, loader, node):
        (tag, value) = loader.construct_mapping(node).popitem()
        return cls(tag, value)

class _AnswerList(_ItemList): # pylint: disable=R0901
    """Answers list. Represents attributes and methods for answers."""
    yaml_tag = u'!Answers'

    def __setitem__(self, key, item):
        if key in self:
            self[key].value = item
        else:
            logger.debug('Creating new answer item.')
            answer = _Answer(key, item)
            self._items.append(answer)

    def __delitem__(self, item):
        item = self.__getitem__(item)
        self._items.remove(item)

_AnswerType = Tuple[str, Union[Message, List[Message]]]

class Form(YAMLObject, metaclass=ABCYamlMeta):
    """Dating form class."""
    _questions: _QuestionList = _QuestionList()

    yaml_tag = u'!Form'

    def __init__(self, *args, **kwargs): # pylint: disable=W0613
        self._answers = _AnswerList()

        self._status: str = FormStatus.BLOCKING.name
        self._note: str = str()

    @property
    def questions(self) -> _QuestionList:
        """Questions list."""
        return self._questions

    @property
    def answers(self) -> _AnswerList:
        """Answers list."""
        return self._answers

    def _format_answer(self, value: _AnswerType) -> Any:
        try:
            question = self._questions[value[0]]
        except KeyError as exc:
            raise AnswerError('No question found.') from exc

        reply = value[1]
        if question.question_type == QuestionType.DIGITS:
            try:
                data = int(reply.text)
            except ValueError as exc:
                raise AnswerError('Answer is not digits.') from exc
        elif question.question_type == QuestionType.TEXT:
            if not reply.text:
                raise AnswerError('Answer is not text.')
            data = reply.text
        elif question.question_type == QuestionType.PHOTO:
            data = []
            for msg in reply:
                if not msg.photo:
                    raise AnswerError('Answer is not photo.')
                data.append(msg.photo[-1].file_id)
        elif question.question_type == QuestionType.AUDIO:
            if reply.text:
                data = (False, reply.text)
            elif reply.audio:
                data = (True, [reply.audio.file_id])
            else:
                raise AnswerError('Answer is not audio.')
        return data

    @answers.setter
    def answers(self, value: _AnswerType) -> None:
        data = self._format_answer(value)

        if not value[0] in self._answers:
            self._answers.append(_Answer(value[0], data))
        else:
            self._answers[value[0]] = data

    @classmethod
    def load_questions(cls, questions: List[_Question]) -> None:
        """Load questions list from directory."""
        logger.info('Loading questions.')
        for question in questions:
            if not isinstance(question, _Question):
                raise TypeError
            logger.debug(vars(question))
        cls._questions = _QuestionList(questions)

    @property
    def status(self) -> FormStatus:
        """Form status Enum."""
        for question in [q for q in self._questions if q.required]:
            if question not in self._answers:
                self._status = FormStatus.BLOCKING.name
                return FormStatus.BLOCKING

        if self._status == FormStatus.BLOCKING.name:
            self._status = FormStatus.IDLE.name
            return FormStatus.IDLE
        return FormStatus[self._status]

    @status.setter
    def status(self, value: FormStatus) -> None:
        logger.debug(f'Setting new status to {str(self)}: {value.name}')
        self._status = value.name

    @property
    def note(self) -> str:
        """Admins note."""
        return self._note

    @note.setter
    def note(self, value) -> None:
        self._note = value

    def _print_header(self) -> str:
        text = (
            f"{self.answers['name'].value}"
            f"({self.answers['age'].value}), "
            f"{self.answers['place'].value}"
        )
        if self.answers['self']:
            text += f"\n\n{self.answers['self'].value}"
        return utils.helpers.escape_markdown(text, 2)

    def print_body(self) -> List[str]:
        """Prints form body to be sent."""
        items = [self._print_header()]
        delim = '\n\n'

        for answer in self.answers:
            # These questions are part of a header
            if answer in _BASE_QUESTIONS or answer in _FINAL_QUESTIONS:
                continue
            question = utils.helpers.escape_markdown(self._questions[answer].value, 2)
            answer = utils.helpers.escape_markdown(answer.value, 2)
            item = delim.join((f'*{question}*', answer))
            items.append(item)

        # Print soundtrack as text
        if 'soundtrack' in self.answers:
            if not self.answers['soundtrack'].value[0]:
                question = utils.helpers.escape_markdown('Soundtrack: ')
                answer = self.answers['soundtrack'].value[1]
                item = ''.join((f'*{question}*', answer))
                items.append(item)

        # Add nick
        items.append(f'*Ник*: {self.nick()}')

        messages = ['']
        for item in items:
            update_len = len(messages[-1]) + len(delim) + len(item)
            if update_len > constants.MAX_MESSAGE_LENGTH:
                messages.append(item)
            else:
                messages[-1] += delim + item
        return messages

    def print_status(self) -> str:
        """Returns this form status string."""
        qcount = 0
        for question in self._questions:
            if question.required and question not in self._answers:
                qcount += 1

        # Update status
        status = self.status

        text = ''
        if status in (FormStatus.BLOCKING, FormStatus.IDLE):
            text += (
                f'Отвечено вопросов: {len(self._answers)} из {len(self._questions)}'
            )
            if status == FormStatus.BLOCKING:
                text += f' (ещё {qcount} обязательных)'
            text += '\n'
        text += f'Статус анкеты: {status.value}'

        if self._note and status == FormStatus.RETURNED:
            text += f'\n\nПримечание админов: {self._note}'
        return text

    @abstractmethod
    def nick(self) -> str:
        """Get nick to sign the form."""

    @classmethod
    def to_yaml(cls, dumper, data: Form):
        mapping = {
            'answers': data.answers,
            'status': data.status.name,
            'note': data.note,
        }
        return dumper.represent_mapping(cls.yaml_tag, mapping)

    @classmethod
    def from_yaml(cls, loader, node) -> Form:
        mapping = loader.construct_mapping(node)
        data = cls.__new__(cls)

        for key, val in mapping.items():
            setattr(data, f'_{key}', val)
        return data
