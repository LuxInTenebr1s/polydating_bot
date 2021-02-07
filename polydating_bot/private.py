import logging
import html
import json
import traceback
import decorator

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

@decorator.decorator
def state(func, back=None, answer='', *args, **kwargs):
    user_data = UserData.from_context(args[1])
    if back:
        user_data.back = back
    user_data.update_context(args[1])

    if args[0].callback_query and answer != False:
        args[0].callback_query.answer(answer)
    elif args[0].message:
        user_data.clear_messages()
    else:
        raise ValueError("Unknown state: {args[0]}")

    return func(*args, *kwargs)

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

def stop(update: Update, context: CallbackContext) -> None:
    pass

TG_TRANSLATE = str.maketrans({
    '.': r'\.',
    '!': r'\!',
    '(': r'\(',
    ')': r'\)',
    '-': r'\-',
    '*': r'\*',
    '_': r'\_',
})

HELP = str().join(
    (f'Привет! Я бот, который поможет тебе создать и опубликовать собственную ',
     f'анкету.\n\n',
     """"""
     f'Для начала попробуй её заполнить: прочитай правила, ответь на вопросы и ',
     f'прикрепи файлы (фото и аудио).\n\n',
     """"""
     f'После этого воспользуйся разделом \'Управление анкетой\' и отправь ',
     f'заполненную анкету админам @PolyDatings. Анкета будет проверена на ',
     f'предмет соблюдения правил и опубликована в канале.\n\n',
     f'Анкета и все твои данные могут быть удалены в любой момент: используй ',
     f'команду /delete или выбери опцию \'Удалить анкету\' в разделе ',
     f'\'Управление анкетой\'.\n\n',
     """"""
     f'Список доступных команд:\n',
     f'/start - возвращение в начало\n',
     f'/впистуябольшенепридумла - хех)0)',
)).translate(TG_TRANSLATE)

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

    update.message.reply_text(text=HELP, parse_mode=ParseMode.MARKDOWN_V2)
    return select_level(update, context)

@state()
def select_level(update: Update, context: CallbackContext) -> None:
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

@state(back=select_level)
def show_help(update: Update, context: CallbackContext):
    text = str().join((
        f'Позже здесь появятся правила и ссылки на более другие документы:\n\n',
        f'За любой помощью обращайтесь к разработчику бота: @srLuxint'
    ))
    button = InlineKeyboardButton(text='Назад', callback_data=str(BACK))
    keyboard = InlineKeyboardMarkup.from_button(button)

    user_data = UserData.from_context(context)
    user_data.print_messages({'text': text, 'reply_markup': keyboard})
    return SELECT_ACTION

@state(back=select_level)
def manage_form(update: Update, context: CallbackContext):
    text = (
        f'Выбери, что ты хочешь сделать с анкетой:'
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

def send_form(update: Update, context: CallbackContext):
    update.callback_query.answer(f'Анкета успешно отправлена!')
    return manage_form(update, context)

def delete_form(update: Update, context: CallbackContext):
    update.callback_query.answer(f'Анкета успешно удалена.')
    return manage_form(update, context)

@state(back=select_level)
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

    user_data = UserData.from_context(context)
    user_data.print_messages({'text': text, 'reply_markup': keyboard})
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

    user_data.update_context(context)
    user_data.current_question += 1
    return ask_question(update, context)

def shift_question(update: Update, context: CallbackContext):
    user_data = UserData.from_context(context)
    if update.callback_query.data == str(NEXT_QUESTION):
        user_data.current_question += 1
    elif update.callback_query.data == str(PREV_QUESTION):
        user_data.current_question -= 1
    else:
        logger.error(f'Incorrect state! IT SHOULD NEVER HAPPEN!')
        raise ValueError(f'Incorrect converstation state: {update.callback_query.data}')
    return ask_question(update, context)

@state(back=edit_form)
def ask_question(update: Update, context: CallbackContext) -> None:
    user_data = UserData.from_context(context)
    bot_data = BotData.from_context(context)

    text = ['', 'Нет ответа']
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

    text[0] = text[0].translate(TG_TRANSLATE)
    user_data.print_messages(
            {'text': f'*{text[0]}*', 'parse_mode': ParseMode.MARKDOWN_V2},
            {'text': text[1], 'reply_markup': keyboard}
    )
    return ANSWER_QUESTION

@state(back=edit_form)
def append_files(update: Update, context: CallbackContext):
    text = (
        f'Выбери тип файла, который ты хочешь прикрепить:'
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

@state(back=append_files)
def append_sound(update: Update, context: CallbackContext):
    text = (
        f'Прикрепите саундтрек/перешлите сообщение от музыкального бота ',
        f'или напишите название саундтрека.'
    )
    button = InlineKeyboardButton(text='Назад', callback_data=str(BACK))
    keyboard = InlineKeyboardMarkup.from_button(button)

    user_data = UserData.from_context(context)
    user_data.print_messages({'text': text, 'reply_markup': keyboard})
    return APPEND_SOUND

def save_sound(update: Update, context: CallbackContext):
    return append_files(update, context)

@state(back=append_files)
def append_photos(update: Update, context: CallbackContext):
    text = (
        'Прикрепите до пяти (5) фото одним сообщением.'
    )
    button = InlineKeyboardButton(text='Назад', callback_data=str(BACK))
    keyboard = InlineKeyboardMarkup.from_button(button)

    user_data = UserData.from_context(context)
    user_data.print_messages({'text': text, 'reply_markup': keyboard})
    return APPEND_PHOTOS

def save_photos(update: Update, context: CallbackContext):
    user_data = UserData.from_context(context)
    logger.debug(f'Saving photos now: {update.message}')
    for idx, photo in enumerate(update.message.photo):
        logger.info(f'Downloading photo: {photo}')
        photo.get_file().download(custom_path=f'{user_data.directory()}/photo{idx}')

    return append_files(update, context)

def back(update: Update, context: CallbackContext) -> None:
    user_data = UserData.from_context(context)
    if user_data.back:
        logger.debug(f'returning back: {user_data.back}')
        return user_data.back(update, context)
    else:
        return select_level(update, context)

def add_private_commands(dispatcher: Dispatcher) -> None:
    select_level_handlers = [
        CallbackQueryHandler(show_help, pattern=f'^{SHOW_HELP}$'),
        CallbackQueryHandler(edit_form, pattern=f'^{EDIT_FORM}$'),
        CallbackQueryHandler(manage_form, pattern=f'^{MANAGE_FORM}$'),
    ]

    select_action_handlers = [
        CallbackQueryHandler(ask_question, pattern=f'^{ANSWER_QUESTION}$'),
        CallbackQueryHandler(append_files, pattern=f'^{APPEND_FILES}$'),
        CallbackQueryHandler(append_sound, pattern=f'^{APPEND_SOUND}$'),
        CallbackQueryHandler(append_photos, pattern=f'^{APPEND_PHOTOS}$'),
        CallbackQueryHandler(manage_form, pattern=f'^{MANAGE_FORM}$'),
        CallbackQueryHandler(send_form, pattern=f'^{SEND_FORM}$'),
        CallbackQueryHandler(delete_form, pattern=f'^{DELETE_FORM}$'),
    ]

    answer_question_handlers = [
        CallbackQueryHandler(shift_question, pattern=f'^{PREV_QUESTION}$|^{NEXT_QUESTION}$'),
        MessageHandler(Filters.text, save_answer),
    ]

    fallback_handlers = [
        CommandHandler('stop', stop),
        CallbackQueryHandler(back, pattern=f'^{BACK}$'),
    ]

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_LEVEL: select_level_handlers,
            SELECT_ACTION: select_action_handlers,
            ANSWER_QUESTION: answer_question_handlers,
            APPEND_PHOTOS: [MessageHandler(Filters.photo, save_photos)],
            APPEND_SOUND: [MessageHandler(Filters.all, save_sound)],
        },
        fallbacks=fallback_handlers
    )

    dispatcher.add_handler(conv_handler)
