from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
    CallbackContext,
)

SELECTING_ACTION, EDIT_FORM, SHOW_STATUS, SEND_FORM, DELETE_FORM = map(chr, range(5))

def start(update: Update, context: CallbackContext) -> None:
    text = (
        'Для работы с ботом выбери один из вариантов:'
    )
    buttons = [
        [
            InlineKeyboardButton(text='Создание (изменение) анкеты', callback_data=str(EDIT_FORM)),
            InlineKeyboardButton(text='Управление анкетой', callback_data=str(SHOW_STATUS)),
        ],
        [
            InlineKeyboardButton(text='Отправить анкету', callback_data=str(SEND_FORM)),
            InlineKeyboardButton(text='Удалить анкету', callback_data=str(DELETE_FORM)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.message.reply_text(
        'Привет! Попробуй воспользоваться моим ботом и отправь свою анкету.'
    )
    update.message.reply_text(text=text, reply_markup=keyboard)
    return SELECTING_ACTION

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
    return EDITING_FORM

def answer_questions(update: Update, context: CallbackContext) -> None:
    :
