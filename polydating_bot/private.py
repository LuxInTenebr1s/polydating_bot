import logging
import html
import json
import traceback

from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    ParseMode,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
    Dispatcher
)

import userdata
import botdata
import chatdata

SELECT_ACTION, EDIT_FORM, SHOW_STATUS, SEND_FORM, DELETE_FORM, SHOW_HELP = map(chr, range(5))
ANSWER_QUESTIONS, APPEND_FILES, NEXT_QUESTION, PREV_QUESTION = map(chr, range(5, 9))
BACK, STOP = map(chr, range(9, 11))

logger = logging.getLogger(__name__)

def debug(update: Update, context: CallbackContext) -> None:
    message = (
        f'<pre>update = {html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>user_data = {html.escape(json.dumps(context.user_data, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>chat_data = {html.escape(json.dumps(context.chat_data, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
    )
    update.message.reply_text(text=message, parse_mode=ParseMode.HTML)

def stop(update: Updater, context: CallbackContext) -> None:
    pass

def start(update: Update, context: CallbackContext) -> None:
    logger.debug(f'{update.message.text}')
    context.user_data['data'] = userdata.UserData(update.message.chat)
    context.chat_data['data'] = chatdata.ChatData(update.message.chat)
    logger.debug(f'Created new user data: {update.message.chat.id}')
    try:
        data: botdata.BotData = context.bot_data['data']
        data.owner = (context.args[0], update.message.chat.id)
    except:
        pass

    text = (
        'Для работы с ботом выберите один из вариантов:'
    )
    buttons = [
        [
            InlineKeyboardButton(text='Создание (изменение) анкеты', callback_data=str(EDIT_FORM)),
            InlineKeyboardButton(text='Управление анкетой', callback_data=str(SHOW_STATUS)),
        ],
        [
            InlineKeyboardButton(text='Помощь', callback_data=str(SHOW_HELP)),
            InlineKeyboardButton(text='Удалить анкету', callback_data=str(DELETE_FORM)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.message.reply_text(
        'Привет! Попробуй воспользоваться моим ботом и отправь свою анкету.'
    )
    update.message.reply_text(text=text, reply_markup=keyboard)
    return SELECT_ACTION

def editing_form(update: Update, context: CallbackContext) -> None:
    text = (
        'Ответьте на вопросы анкеты или прикрепите файлы (фото и аудио)'
    )
    buttons = [
        [
            InlineKeyboardButton(text='Заполнить анкету (вопросы)', callback_data=str(ANSWER_QUESTIONS)),
            InlineKeyboardButton(text='Прикрепить файлы', callback_data=str(APPEND_FILES)),
        ],
        [
            InlineKeyboardButton(text='Назад', callback_data=str(BACK)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.message.reply_text(text=text, reply_markup=keyboard)
    return EDIT_FORM

def answer_questions(update: Update, context: CallbackContext) -> None:
    bot_data: botdata.BotData  = context.bot_data['data']
    user_data: userdata.UserData = context.user_data['data']

    question_idx = 0
    if update.callback_query.data() == str(NEXT_QUESTION):
        question_idx = (question_idx + 1) % len(bot_data.questions)
    elif update.callback_query.data() == str(PREV_QUESTION):
        question_idx = (question_idx + len(bot_data.questions) - 1) \
                       % len(bot_data.questions)
    question = bot_data.questions.items()[question_idx]

    act_answer = str
    if user_data.answers[question[0]]:
        act_answer = f'user_data.answers[question[0]]'
    else:
        act_answer = f'Нет ответа.'

    button = [
        [
            InlineKeyboardButton(text='Следующий', callback_data=str(NEXT_QUESTION)),
            InlineKeyboardButton(text='Предыдущий', callback_data=str(PREV_QUESTION)),
        ],
        [
            InlineKeyboardButton(text='Назад', callback_data=str(BACK)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(button)

    update.message.reply_text(text=question[1])
    update.message.reply_text(text=act_answer, reply_markup=keyboard)

def add_private_commands(dispatcher: Dispatcher) -> None:
    selection_handlers = ()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_ACTION: selection_handlers,
            STOP: [CommandHandler('start', start)],
        },
        fallbacks=[CommandHandler('stop', stop)],
    )

    dispatcher.add_handler(conv_handler)
