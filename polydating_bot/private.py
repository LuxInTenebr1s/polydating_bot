import logging
import html
import json
import traceback

from telegram import (
    Bot,
    Message,
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

from userdata import UserData
from botdata import BotData
import chatdata

SELECT_LEVEL, SELECT_ACTION, ANSWER_QUESTION, APPEND_FILES, APPEND_PHOTOS, APPEND_SOUND, EDIT_FORM, SEND_FORM, DELETE_FORM, NEXT_QUESTION, PREV_QUESTION, BACK, STOP, MANAGE_FORM, SHOW_HELP= range(15)

REPLY_AGE, REPLY_NAME, REPLY_PLACE = range(15, 18)
logger = logging.getLogger(__name__)

#order = [
#    SELECT_ACTION,
#    [ SHOW_HELP, [EDIT_FORM, MANAGE_FORM, ]

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
    UserData(update.message.chat).update_context(context)
    context.chat_data['data'] = chatdata.ChatData(update.message.chat)
    logger.debug(f'Created new user data: {update.message.chat.id}')
    try:
        bot_data = BotData.from_context(context)
        bot_data.owner = (context.args[0], update.message.chat.id)
    except:
        pass

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

    update.message.reply_text(
        'Привет! Попробуй воспользоваться моим ботом и отправь свою анкету.'
    )
    update.message.reply_text(text=text, reply_markup=keyboard)
    return SELECT_LEVEL

def edit_form(update: Update, context: CallbackContext) -> None:
    text = (
        'Ответьте на вопросы анкеты или прикрепите файлы (фото и аудио)'
    )
    buttons = [
        [
            InlineKeyboardButton(text='Заполнить анкету (вопросы)', callback_data=str(ANSWER_QUESTION)),
            InlineKeyboardButton(text='Прикрепить файлы', callback_data=str(APPEND_FILES)),
        ],
        [
            InlineKeyboardButton(text='Назад', callback_data=str(BACK)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text, reply_markup=keyboard)
    return SELECT_ACTION

def save_answer(update: Update, context: CallbackContext) -> None:
    user_data = UserData.from_context(context)
    bot_data = BotData.from_context(context)
    reply = update.message.text

    if user_data.current_question == UserData.NAME:
        user_data.name = reply
    elif user_data.current_question == UserData.AGE:
        user_data.age = int(reply)
    elif user_data.current_question == UserData.PLACE:
        user_data.place = reply
    else:
        tag = bot_data.question_tag_from_idx[user_data.current_question]
        user_data.answers[tag] = reply

    user_data.current_question += 1
    ask_question(update, context)
    return ANSWER_QUESTION

def shift_question(update: Update, context: CallbackContext):
    user_data = UserData.from_context(context)
    if update.callback_query.data == str(NEXT_QUESTION):
        user_data.current_question += 1
    elif update.callback_query.data == str(PREV_QUESTION):
        user_data.current_question -= 1
    else:
        logger.error(f'Incorrect state! IT SHOULD NEVER HAPPEN!')
        raise ValueError(f'Incorrect converstation state: {update.callback_query.data}')

    ask_question(update, context)
    return ANSWER_QUESTION

def ask_question(update: Update, context: CallbackContext) -> None:
    user_data = UserData.from_context(context)
    bot_data = BotData.from_context(context)

    text = ['', 'Нет ответа',]
    if user_data.current_question == UserData.NAME:
        text[0] = 'Как Вас зовут?'
        if user_data.name:
            text[1] = user_data.name
    elif user_data.current_question == UserData.AGE:
        text[0] = 'Сколько Вам лет?'
        if user_data.age:
            text[1] = str(user_data.age)
    elif user_data.current_question == UserData.PLACE:
        text[0] = 'Где Вы живёте?'
        if user_data.place:
            text[1] = user_data.place
    else:
        tag = bot_data.question_tag_from_idx(user_data.current_question)
        text[0] = bot_data.questions[tag]
        if user_data.answers.get(tag):
            text[1] = user_data.answers[tag]

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

    if update.callback_query:
        update.callback_query.answer()

    text[0] = text[0].translate(str.maketrans({'_': r'\_', '*': r'\*'}))
    logger.debug(f'Question: *{text[0]}*')
    user_data.msg_one = context.bot.send_message(user_data.id, f'*{text[0]}*',
                                                 parse_mode=ParseMode.MARKDOWN_V2)
    user_data.msg_two = context.bot.send_message(user_data.id, text[1],
                                                 reply_markup=keyboard)
    return ANSWER_QUESTION

def test(update: Update, context: CallbackContext):
    return SELECT_ACTION

def manage_form(update: Update, context: CallbackContext):
    return STOP

def show_help(update: Update, context: CallbackContext):
    return STOP

def append_files(update: Update, context: CallbackContext):
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

    update.callback_query.answer()
    update.callback_query.edit_message_reply_markup(keyboard)

    return SELECT_ACTION

def append_sound(update: Update, context: CallbackContext):
    return STOP

def append_photos(update: Update, context: CallbackContext):
    text = (
        'Прикрепите до пяти (5) фото одним сообщением.'
    )
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)

    return APPEND_PHOTOS

def save_photos(update: Update, context: CallbackContext):
    user_data = UserData.from_context(context)
    logger.debug(f'Saving photos now: {update.message}')
    for idx, photo in enumerate(update.message.photo):
        logger.info(f'Downloading photo: {photo}')
        photo.get_file().download(custom_path=f'{user_data.directory()}/photo{idx}')

    append_files(update, context)
    return SELECT_ACTION

def add_private_commands(dispatcher: Dispatcher) -> None:
#    edit_form_conv = ConversationHandler(
#        entry_points=[CallbackQueryHandler(editing_form,
#                                           pattern=f'^{EDIT_FORM}$')],
#        states={
#            EDIT_FORM: [
#                CallbackQueryHandler(answer_questions,
#                                     pattern=f'^{ANSWER_QUESTIONS}$'),
#            ],
#        },
#        fallbacks=[CommandHandler('stop', stop)],
#    )

##    selection_handlers = (
##            edit_form_conv,
##    )
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_LEVEL: [
                CallbackQueryHandler(edit_form, pattern=f'^{EDIT_FORM}$'),
                CallbackQueryHandler(manage_form, pattern=f'^{MANAGE_FORM}$'),
                CallbackQueryHandler(show_help, pattern=f'^{SHOW_HELP}$'),
            ],
            SELECT_ACTION: [
                CallbackQueryHandler(ask_question, pattern=f'^{ANSWER_QUESTION}$'),
                CallbackQueryHandler(append_files, pattern=f'^{APPEND_FILES}$'),
                CallbackQueryHandler(append_sound, pattern=f'^{APPEND_SOUND}$'),
                CallbackQueryHandler(append_photos, pattern=f'^{APPEND_PHOTOS}$'),
            ],
            ANSWER_QUESTION: [
                CallbackQueryHandler(shift_question, pattern=f'^{PREV_QUESTION}$|^{NEXT_QUESTION}$'),
                MessageHandler(Filters.text, save_answer),
            ],
            APPEND_PHOTOS: [
                MessageHandler(Filters.photo, save_photos),
            ],
#            DESCRIBE_SELF: [
#
#            ],
        },
        fallbacks=[CommandHandler('stop', stop)],
    )

    dispatcher.add_handler(conv_handler)
