#!/usr/bin/env python3
"""Chat data module."""

from __future__ import annotations

import logging

from typing import (
    Dict,
    List,
    Optional,
    Union
)

from telegram import (
    Chat,
    InputMediaPhoto,
    InputMediaAudio,
    Message,
    TelegramError,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from polydating_bot import (
    NoMediaError
)
from polydating_bot.data import (
    Data,
    DataType,
    UserData,
    QuestionType
)

logger = logging.getLogger(__name__)

class ChatData(Data):
    """Chat data class."""
    yaml_tag = u'!ChatData'

    _MSG_COUNT = 2

    def __init__(self, chat: Chat):
        super().__init__(chat)

        self._forms: Dict[int, List[int]] = dict()
        self._error: Optional[int] = None
        self._msgs: List[Optional[int]] = [None] * self._MSG_COUNT
        self._needs_update: bool = False

    @classmethod
    def data_type(cls) -> DataType:
        return DataType.CHAT

    @classmethod
    def data_mapping(cls) -> Dict:
        return {
            'ids': ['_forms', '_error', '_msgs', '_needs_update'],
        }

    @property
    def __forms(self) -> Dict[int, List[int]]:
        return self._forms

    @__forms.setter
    def __forms(self, value: (int, Union[List[Message], Message])) -> None:
        user_id = value[0]
        try:
            value = iter(value[1])
        except TypeError:
            value = (value[1],)

        self.delete_form(user_id)
        self._forms[user_id] = [msg.message_id for msg in value]

    @property
    def needs_update(self) -> bool:
        """Last user message ID."""
        return self._needs_update

    @needs_update.setter
    def needs_update(self, value: bool) -> None:
        self._needs_update = value

    def delete_form(self, user_id: int) -> None:
        """Delete all user media and other form data from current chat."""
        if not self._forms.get(user_id):
            return

        for message_id in self._forms[user_id]:
            self._bot.deleteMessage(self._id, message_id)
        del self._forms[user_id]

    def _show_button(self, user_id: int, callback_data: str):
        keyboard = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(text='Скрыть', callback_data=str(callback_data))
        )

        self._bot.editMessageReplyMarkup(
            self._id,
            self._forms[user_id][-1],
            reply_markup=keyboard
        )

    def _send_media(self,
                   data: UserData,
                   media_type: QuestionType,
                   reply_id: Optional[int] = None
    ) -> List[Message]:
        media_cls = None
        file_ids = []
        for answer in data.answers:
            if data.questions[answer].question_type == media_type:
                if media_type == QuestionType.AUDIO and answer.value[0]:
                    file_ids.extend(answer.value[1])
                    media_cls = InputMediaAudio
                elif media_type == QuestionType.PHOTO:
                    file_ids.extend(answer.value)
                    media_cls = InputMediaPhoto
                else:
                    raise NoMediaError

        if not media_cls:
            logger.debug(f'No media of type: {media_type}')
            raise NoMediaError

        media = [media_cls(fid) for fid in file_ids]
        return self._bot.sendMediaGroup(self._id, media=media, reply_to_message_id=reply_id)

    def send_media(self,
                   data: UserData,
                   media_type: QuestionType,
                   callback_data: str = None
    ) -> None:
        """Send media to chat."""
        self.__forms = (data.id, self._send_media(data, media_type))
        if callback_data:
            self._show_button(data.id, callback_data)

    def send_form(self, data: UserData, callback_data: str = None) -> None:
        """Send form to chat."""
        msgs = []
        for text_item in data.print_body():
            msgs.append(self._bot.sendMessage(
                self._id,
                text=text_item,
                parse_mode='MarkdownV2')
            )

        reply_id = msgs[0].message_id
        for media_type in (QuestionType.PHOTO, QuestionType.AUDIO):
            try:
                media = self._send_media(
                    data,
                    media_type,
                    reply_id=reply_id
                )
                msgs.extend(media)
            except NoMediaError:
                pass
        self.__forms = (data.id, msgs)

        if callback_data:
            self._show_button(data.id, callback_data)

    def print_error(self, text: str) -> None:
        """Print error message to chat."""
        self.clear_error()
        message = self._bot.sendMessage(self._id, text=f'Ошибка: {text}')

        self._error = message.message_id

    def clear_error(self) -> None:
        """Clear error message."""
        if self._error:
            self._bot.deleteMessage(self.id, self._error)
            self._error = None

    def clear_messages(self) -> None:
        """Clear bot messages."""
        for idx, msg in enumerate(self._msgs):
            try:
                self._msgs[idx] = None
                self._bot.delete_message(self.id, msg)
            except TelegramError:
                pass
        self._needs_update = False

    def print_messages(self, *args: Dict) -> None:
        """Print messages. Pass each message argument as keyword dictionary."""
        if self._needs_update:
            self.clear_messages()

        for idx, msg in enumerate(self._msgs):
            try:
                kwargs = args[idx]
            except IndexError:
                kwargs = None

            if not kwargs:
                if msg:
                    self._msgs[idx] = None
                    self._bot.delete_message(self.id, msg)
                continue

            if msg:
                try:
                    message = self._bot.edit_message_text(
                        chat_id=self.id,
                        message_id=msg,
                        **kwargs
                    )
                    self._msgs[idx] = message.message_id
                except TelegramError as exc:
                    logger.debug(exc)
            else:
                message = self._bot.send_message(self.id, **kwargs)
                self._msgs[idx] = message.message_id
