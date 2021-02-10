#!/usr/bin/env python3
# pylint: disable=W0702,W0613
"""Module with private chats business logic."""

import logging
import decorator

from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    ParseMode,
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
    Dispatcher
)

from .data.userdata import (
    UserData
)
from .data.botdata import (
    BotData
)
from .data import (
    chatdata
)
#    botdata,
#    chatdata,

(SHOW_HELP,
 SELECT_LEVEL,
 SELECT_ACTION,
 ANSWER_QUESTION,
 APPEND_FILES,
 APPEND_PHOTOS,
 APPEND_SOUND,
 EDIT_FORM,
 SEND_FORM,
 DELETE_FORM,
 NEXT_QUESTION,
 PREV_QUESTION,
 BACK,
 STOP,
 MANAGE_FORM
) = map(chr, range(15))

logger = logging.getLogger(__name__)

def _k(update: Update, context: CallbackContext, udata: UserData) -> None:
    pass

@decorator.decorator
def _state(func, back=None, answer='', *args, **kwargs): # pylint: disable=W1113
    user_data = UserData.from_context(args[1])
    if back:
        user_data.back = back
    user_data.update_context(args[1])

    if args[0].callback_query and answer is not None:
        args[0].callback_query.answer(answer)
    elif args[0].message:
        user_data.clear_messages()
    else:
        raise ValueError(f'Unknown state: {args[0]}')

    return func(*args, *kwargs)

def _stop(update: Update, context: CallbackContext) -> None: # pylint: disable=W0613
    pass

TG_TRANSLATE = str.maketrans({
    '.': r'\.',
    '!': r'\!',
    '(': r'\(',
    ')': r'\)',
    '-': r'\-',
    '*': r'\*',
    '_': r'\_',
    '#': r'\#',
})

HELP = (
    'Привет! Я бот, который поможет тебе создать и опубликовать собственную '
    'анкету.\n\n'
    """"""
    'Для начала попробуй её заполнить: прочитай правила, ответь на вопросы и '
    'прикрепи файлы (фото и аудио).\n\n'
    """"""
    'После этого воспользуйся разделом \'Управление анкетой\' и отправь '
    'заполненную анкету админам @PolyDatings. Анкета будет проверена на '
    'предмет соблюдения правил и опубликована в канале.\n\n'
    'Анкета и все твои данные могут быть удалены в любой момент: используй '
    'команду /delete или выбери опцию \'Удалить анкету\' в разделе '
    '\'Управление анкетой\'.\n\n'
    """"""
    'Список доступных команд:\n'
    '/start - возвращение в начало\n'
    '/впистуябольшенепридумла - хех)0)'
).translate(TG_TRANSLATE)

def _start(update: Update, context: CallbackContext) -> None:
    logger.debug(f'{update.message.text}')

    try:
        UserData.from_context(context)
    except IndexError:
        UserData(update.message.chat).update_context(context)
        context.chat_data['data'] = chatdata.ChatData(update.message.chat)
        logger.debug(f'Created new user data: {update.message.chat.id}')

    try:
        bot_data = BotData.from_context(context)
        bot_data.owner = (context.args[0], update.message.chat.id)
    except:
        pass

    update.message.reply_text(text=HELP, parse_mode=ParseMode.MARKDOWN_V2)
    return _select_level(update, context)

@_state
def _select_level(update: Update, context: CallbackContext) -> None:
    text = (
        'Для работы с ботом выберите один из вариантов:'
    )
    buttons = [
        [
            InlineKeyboardButton(text='Изменение анкеты', callback_data=str(EDIT_FORM)),
            InlineKeyboardButton(text='Управление анкетой', callback_data=str(MANAGE_FORM)),
        ],
        [
            InlineKeyboardButton(text='Помощь', callback_data=str(SHOW_HELP)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    user_data = UserData.from_context(context)
    user_data.print_messages({'text': text, 'reply_markup': keyboard})
    return SELECT_LEVEL

@_state(back=_select_level)
def _show_help(update: Update, context: CallbackContext):
    text = (
        'Позже здесь появятся правила и ссылки на более другие документы:\n\n'
        'За любой помощью обращайтесь к разработчику бота: @srLuxint'
    )
    button = InlineKeyboardButton(text='Назад', callback_data=str(BACK))
    keyboard = InlineKeyboardMarkup.from_button(button)

    user_data = UserData.from_context(context)
    user_data.print_messages({'text': text, 'reply_markup': keyboard})
    return SELECT_ACTION

@_state(back=_select_level)
def _manage_form(update: Update, context: CallbackContext):
    text = (
        'Выбери, что ты хочешь сделать с анкетой:'
    )
    buttons = [
        [
            InlineKeyboardButton(text='Отправить анкету', callback_data=str(SEND_FORM)),
            InlineKeyboardButton(text='Удалить анкету', callback_data=str(DELETE_FORM)),
        ],
        [
            InlineKeyboardButton(text='Назад', callback_data=str(BACK)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    user_data = UserData.from_context(context)
    user_data.print_messages(
            {'text': text},
            {'text': user_data.show_status(), 'reply_markup': keyboard}
    )
    return SELECT_ACTION

def _send_form(update: Update, context: CallbackContext):
    update.callback_query.answer('Анкета успешно отправлена!')
    return _manage_form(update, context)

def _delete_form(update: Update, context: CallbackContext):
    update.callback_query.answer('Анкета успешно удалена.')
    return _manage_form(update, context)

@_state(back=_select_level)
def _edit_form(update: Update, context: CallbackContext, user_data: UserData = None) -> None:
    text = (
        'Ответьте на вопросы анкеты или прикрепите файлы (фото и аудио)'
    )
    buttons = [
        [
            InlineKeyboardButton(text='Ответить на вопросы', callback_data=str(ANSWER_QUESTION)),
            InlineKeyboardButton(text='Прикрепить файлы', callback_data=str(APPEND_FILES)),
        ],
        [
            InlineKeyboardButton(text='Назад', callback_data=str(BACK)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    user_data = UserData.from_context(context)
    user_data.print_messages({'text': text, 'reply_markup': keyboard})
    return SELECT_ACTION

def _save_answer(update: Update, context: CallbackContext) -> None:
    user_data = UserData.from_context(context)
    bot_data = BotData.from_context(context)

    question = bot_data.questions[user_data.current_question]
    reply = update.message.text
    try:
        user_data.answers[question.tag] = reply
        user_data.current_question += 1
        user_data.update_context(context)
    except ValueError:
        logger.error('Incorrect value. Try again.')

    return _ask_question(update, context)

def _shift_question(update: Update, context: CallbackContext):
    user_data = UserData.from_context(context)
    if update.callback_query.data == str(NEXT_QUESTION):
        user_data.current_question += 1
    elif update.callback_query.data == str(PREV_QUESTION):
        user_data.current_question -= 1
    else:
        logger.error('Incorrect state! IT SHOULD NEVER HAPPEN!')
        raise ValueError(f'Incorrect converstation state: {update.callback_query.data}')

    return _ask_question(update, context)

@_state(back=_edit_form)
def _ask_question(update: Update, context: CallbackContext) -> None:
    user_data = UserData.from_context(context)
    bot_data = BotData.from_context(context)

    question = bot_data.questions[user_data.current_question]
    text = [question.question, question.note, user_data.answers[question.tag]]

    buttons = [
        [
            InlineKeyboardButton(text='Предыдущий', callback_data=str(PREV_QUESTION)),
            InlineKeyboardButton(text='Следующий', callback_data=str(NEXT_QUESTION)),
        ],
        [
            InlineKeyboardButton(text='Назад', callback_data=str(BACK)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    text[0] = text[0].translate(TG_TRANSLATE)
    text[1] = text[1].translate(TG_TRANSLATE)

    first = f'*{text[0]}*\n'
    first += f'_{text[1]}_' if text[1] else ''
    second = f'{text[2].answer}' if text[2] else 'Не отвечено.'

    user_data.print_messages(
            {'text': first, 'parse_mode': ParseMode.MARKDOWN_V2},
            {'text': second, 'reply_markup': keyboard}
    )
    return ANSWER_QUESTION

@_state(back=_edit_form)
def _append_files(update: Update, context: CallbackContext):
    text = (
        'Выбери тип файла, который ты хочешь прикрепить:'
    )
    buttons = [
        [
            InlineKeyboardButton(text='Добавить фото', callback_data=str(APPEND_PHOTOS)),
            InlineKeyboardButton(text='Добавить аудио', callback_data=str(APPEND_SOUND)),
        ],
        [
            InlineKeyboardButton(text='Назад', callback_data=str(BACK)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    user_data = UserData.from_context(context)
    user_data.print_messages({'text': text, 'reply_markup': keyboard})
    return SELECT_ACTION

@_state(back=_append_files)
def _append_sound(update: Update, context: CallbackContext):
    text = (
        'Прикрепите саундтрек/перешлите сообщение от музыкального бота '
        'или напишите название саундтрека.'
    )
    button = InlineKeyboardButton(text='Назад', callback_data=str(BACK))
    keyboard = InlineKeyboardMarkup.from_button(button)

    user_data = UserData.from_context(context)
    user_data.print_messages({'text': text, 'reply_markup': keyboard})
    return APPEND_SOUND

def _save_sound(update: Update, context: CallbackContext):
    user_data = UserData.from_context(context)

    if update.message.audio:
        user_data.save_sound(update.message.audio.get_file())
    else:
        user_data.save_sound(update.message.text)
    user_data.update_context(context)

    return _append_files(update, context)

def _save_sound(update: Update, context: CallbackContext):
    return _append_files(update, context)

@_state(back=_append_files)
def _append_photos(update: Update, context: CallbackContext):
    text = (
        'Прикрепите до пяти (5) фото одним сообщением.'
    )
    button = InlineKeyboardButton(text='Назад', callback_data=str(BACK))
    keyboard = InlineKeyboardMarkup.from_button(button)

    user_data = UserData.from_context(context)
    user_data.print_messages({'text': text, 'reply_markup': keyboard})
    return APPEND_PHOTOS

def _save_photos(update: Update, context: CallbackContext):
    queue = context.dispatcher.update_queue

    updates = [update]
    for _ in range(queue.qsize()):
        updates.append(queue.get())

    if len(updates) > 5:
        return _append_photos(update, context)

    photos = []
    for upd in updates:
        if upd.message.photo:
            photos.append(upd.message.photo[-1].get_file())

    user_data = UserData.from_context(context)
    user_data.save_photos(photos)
    user_data.update_context(context)

    return _append_files(update, context)

def _back(update: Update, context: CallbackContext) -> None:
    user_data = UserData.from_context(context)
    if user_data.back:
        logger.debug(f'returning back: {user_data.back}')
        return user_data.back(update, context)
    return _select_level(update, context)

def add_handlers(dispatcher: Dispatcher) -> None:
    """Add handlers for private conversation."""
    select_level_handlers = [
        CallbackQueryHandler(_show_help, pattern=f'^{SHOW_HELP}$'),
        CallbackQueryHandler(_edit_form, pattern=f'^{EDIT_FORM}$'),
        CallbackQueryHandler(_manage_form, pattern=f'^{MANAGE_FORM}$'),
    ]

    select_action_handlers = [
        CallbackQueryHandler(_ask_question, pattern=f'^{ANSWER_QUESTION}$'),
        CallbackQueryHandler(_append_files, pattern=f'^{APPEND_FILES}$'),
        CallbackQueryHandler(_append_sound, pattern=f'^{APPEND_SOUND}$'),
        CallbackQueryHandler(_append_photos, pattern=f'^{APPEND_PHOTOS}$'),
        CallbackQueryHandler(_manage_form, pattern=f'^{MANAGE_FORM}$'),
        CallbackQueryHandler(_send_form, pattern=f'^{SEND_FORM}$'),
        CallbackQueryHandler(_delete_form, pattern=f'^{DELETE_FORM}$'),
    ]

    answer_question_handlers = [
        CallbackQueryHandler(_shift_question, pattern=f'^{PREV_QUESTION}$|^{NEXT_QUESTION}$'),
        MessageHandler(Filters.text, _save_answer),
    ]

    fallback_handlers = [
        CommandHandler('stop', _stop),
        CallbackQueryHandler(_back, pattern=f'^{BACK}$'),
    ]

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', _start)],
        states={
            SELECT_LEVEL: select_level_handlers,
            SELECT_ACTION: select_action_handlers,
            ANSWER_QUESTION: answer_question_handlers,
            APPEND_PHOTOS: [MessageHandler(Filters.photo, _save_photos)],
            APPEND_SOUND: [MessageHandler(Filters.text | Filters.audio, _save_sound)],
        },
        fallbacks=fallback_handlers
    )

    dispatcher.add_handler(conv_handler)
