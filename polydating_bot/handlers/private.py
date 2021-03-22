#!/usr/bin/env python3
# pylint: disable=W0702,W0613,E1120,W1401
"""Module with private chats business logic."""

import logging

import decorator

from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Update,
    ParseMode,
    utils
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

from polydating_bot import (
    MissingDataError,
    AnswerError,
    NoMediaError
)
from polydating_bot.data import (
    UserData,
    BotData,
    ChatData,
    FormStatus,
    QuestionType
)
from polydating_bot.handlers import (
    PRIVATE_GROUP,
    SHOW,
    REMOVE
)

# Available converstation states
(
    SELECT_LEVEL,
    SELECT_ACTION,
    ASK_QUESTION
) = map(chr, range(3))

# Conversation levels
(
    SHOW_HELP,
    ASK_QUESTION,
    MANAGE_FORM
) = map(chr, range(3, 6))

# Ask question actions
(
    PREV_QUESTION,
    NEXT_QUESTION,
    DELETE_ANSWER,
    SHOW_FILE
) = map(chr, range(6, 10))

# Manage form actions
(
    SHOW_FORM,
    SEND_FORM,
    WITHDRAW_FORM,
    DELETE_FORM
) = map(chr, range(10, 14))

# Back action
BACK = chr(14)

# Remove media/form action
REMOVE = chr(15)

logger = logging.getLogger(__name__)

@decorator.decorator
def _state(func, back = None, *args, **kwargs): # pylint: disable=W1113
    chat_data = ChatData.from_context(args[1])
    user_data = UserData.from_context(args[1])
    if back:
        user_data.back = back

    chat_data.clear_error()

    chat_data.delete_form(chat_data.id)

    if args[0].callback_query:
        args[0].callback_query.answer()

    return func(*args, *kwargs)

def _stop(update: Update, context: CallbackContext) -> None: # pylint: disable=W0613
    return ConversationHandler.END

HELP = utils.helpers.escape_markdown(
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
    '/start - начать диалог\n'
    '/stop  - окончить диалог', 2
)

def _start(update: Update, context: CallbackContext) -> None:
    logger.debug(f'{update.message.text}')

    try:
        UserData.from_context(context)
    except MissingDataError:
        UserData(update.message.chat).update_context(context)
        ChatData(update.message.chat).update_context(context)
        logger.debug(f'Created new user data: {update.message.chat.id}')
        update.message.reply_text(text=HELP, parse_mode=ParseMode.MARKDOWN_V2)

    try:
        bot_data = BotData.from_context(context)
        bot_data.owner = (context.args[0], update.message.chat.id)
    except (IndexError, MissingDataError):
        pass

    return _select_level(update, context)

@_state
def _select_level(update: Update, context: CallbackContext) -> None:
    text = (
        'Для работы с ботом выберите один из вариантов:'
    )
    buttons = [
        [
            InlineKeyboardButton(text='Управление анкетой', callback_data=str(MANAGE_FORM)),
        ],
        [
            InlineKeyboardButton(text='Помощь', callback_data=str(SHOW_HELP)),
        ],
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    chat_data = ChatData.from_context(context)
    chat_data.print_messages({'text': text, 'reply_markup': keyboard})
    return SELECT_LEVEL

@_state(back=_select_level)
def _show_help(update: Update, context: CallbackContext):
    text = (
        'Позже здесь появятся правила и ссылки на более другие документы:\n\n'
        'За любой помощью обращайтесь к разработчику бота: @srLuxint'
    )
    button = InlineKeyboardButton(text='Назад', callback_data=str(BACK))
    keyboard = InlineKeyboardMarkup.from_button(button)

    chat_data = ChatData.from_context(context)
    chat_data.print_messages({'text': text, 'reply_markup': keyboard})
    return SELECT_ACTION

@_state(back=_select_level)
def _manage_form(update: Update, context: CallbackContext):
    user_data = UserData.from_context(context)
    chat_data = ChatData.from_context(context)

    answer_button = InlineKeyboardButton(text='Ответить на вопросы',
                                         callback_data=str(ASK_QUESTION))
    show_form_button = InlineKeyboardButton(text='Показать анкету',
                                         callback_data=str(SHOW_FORM))

    buttons = [[], [], []]
    text = str()

    status = user_data.status
    if status == FormStatus.BLOCKING:
        buttons[0].append(
            answer_button
        )
        text = (
            'Заполни анкету для отправки.'
        )
    elif status == FormStatus.IDLE:
        buttons[0].extend(
            (answer_button, show_form_button)
        )
        buttons[1].append(
            InlineKeyboardButton(text='Отправить анкету',
                                         callback_data=str(SEND_FORM))
        )
        text = (
            'Анкета заполнена и готова к отправке на ревью админами.'
        )
    elif status == FormStatus.PENDING:
        buttons[0].append(
            show_form_button
        )
        buttons[1].append(
            InlineKeyboardButton(text='Отозвать анкету',
                                         callback_data=str(WITHDRAW_FORM))
        )
        text = (
            'Анкета отправлена и ожидает ревью. Если хочешь внести правки -- '
            'сначала отзови анкету назад.'
        )
    elif status == FormStatus.PUBLISHED:
        buttons[1].append(
            InlineKeyboardButton(text='Удалить анкету',
                                         callback_data=str(DELETE_FORM))
        )
        text = (
            'Анкета успешно опубликована! Поздравляю. В любой момент ты можешь '
            'удалить её из канала.'
        )
    elif status == FormStatus.RETURNED:
        buttons[0].extend(
            (answer_button, show_form_button)
        )
        buttons[1].append(
            InlineKeyboardButton(text='Отправить анкету',
                                         callback_data=str(SEND_FORM))
        )
        text = (
            'К сожалению, твоя анкета не прошла ревью админами. Ознакомься '
            'с замечаниями и попробуй ещё раз.'
        )

    buttons[2].append(
        InlineKeyboardButton(text='Назад', callback_data=str(BACK))
    )
    keyboard = InlineKeyboardMarkup(buttons)

    logger.debug(f'{text}, {keyboard}')
    chat_data.print_messages(
            {'text': text},
            {'text': user_data.print_status(), 'reply_markup': keyboard}
    )
    return SELECT_ACTION

def _send_form(update: Update, context: CallbackContext):
    user_data = UserData.from_context(context)
    bot_data = BotData.from_context(context)
    bot = Dispatcher.get_instance().bot

    # Send message to all admins chats (chats have negative ID)
    for chat in [c for c in bot_data.admins if c < 0]:
        text = utils.helpers.escape_markdown(
            f'Новая анкета: {user_data.id} \({user_data.mention()}\)'
        )
        keyboard = InlineKeyboardMarkup.from_button(InlineKeyboardButton(
            text='Показать', callback_data=f'{str(SHOW)}{user_data.id}'
        ))
        bot.sendMessage(chat, text=text, reply_markup=keyboard, parse_mode='MarkdownV2')

    # Update form status
    bot_data.pending_forms.append(user_data.id)
    user_data.status = FormStatus.PENDING

    logger.info('New form has been sent: {str(user_data)}')
    update.callback_query.answer('Анкета успешно отправлена!')
    return _manage_form(update, context)

def _withdraw_form(update: Update, context: CallbackContext):
    user_data = UserData.from_context(context)
    bot_data = BotData.from_context(context)

    # Anyway change form status
    user_data.status = FormStatus.BLOCKING
    bot_data.pending_forms.remove(user_data.id)

    update.callback_query.answer('Отправка анкеты отменена.')
    return _manage_form(update, context)

def _delete_form(update: Update, context: CallbackContext):
    bot_data = BotData.from_context(context)
    user_data = UserData.from_context(context)
    try:
        user_data.status = FormStatus.BLOCKING
        channel = ChatData.by_id(bot_data.dating_channel)
    except MissingDataError:
        pass
    else:
        channel.delete_form(user_data.id)

    logger.info(f'Form has been deleted: {str(user_data)}')
    update.callback_query.answer('Анкета успешно удалена.')
    return _manage_form(update, context)

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

def _delete_answer(update: Update, context: CallbackContext):
    user_data = UserData.from_context(context)
    question = user_data.questions[user_data.current_question]
    try:
        del user_data.answers[question]
    except MissingDataError:
        pass
    return _ask_question(update, context)

def _show_media(update: Update, context: CallbackContext):
    user_data = UserData.from_context(context)
    chat_data = ChatData.from_context(context)
    question = user_data.questions[user_data.current_question]

    try:
        chat_data.send_media(user_data, question.question_type)
    except NoMediaError:
        pass

    update.callback_query.answer()
    return ASK_QUESTION

def _question_keyboard(
    show_button: bool = False,
    remove_button: bool = False
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text='Предыдущий', callback_data=str(PREV_QUESTION)),
            InlineKeyboardButton(text='Следующий', callback_data=str(NEXT_QUESTION)),
        ],
        [
            InlineKeyboardButton(text='Назад', callback_data=str(BACK)),
        ],
    ]
    if show_button:
        buttons.insert(1, [InlineKeyboardButton(
            text='Показать',
            callback_data=str(SHOW_FILE)
        )])
    if remove_button:
        buttons.insert(1, [InlineKeyboardButton(
            text='Удалить ответ',
            callback_data=str(DELETE_ANSWER)
        )])
    return InlineKeyboardMarkup(buttons)

def _format_question_text(question) -> str:
    if question.required:
        req = utils.helpers.escape_markdown('\(*\)')
    else:
        req = ''

    if question.note:
        note = f'_{utils.helpers.escape_markdown(question.note, 2)}_'
    else:
        note = ''

    text = (
        f'{req} ',
        f'*{utils.helpers.escape_markdown(question.value, 2)}*\n',
        f'{note}',
    )
    return ''.join(text)

@_state(back=_manage_form)
def _ask_question(update: Update, context: CallbackContext) -> None:
    user_data = UserData.from_context(context)
    chat_data = ChatData.from_context(context)
    question = user_data.questions[user_data.current_question]

    show: bool = False
    remove: bool = False

    try:
        answer = user_data.answers[question].value
    except MissingDataError as exc:
        if question.question_type in (QuestionType.TEXT, QuestionType.DIGITS):
            answer = 'Не отвечено'
        elif question.question_type == QuestionType.AUDIO:
            answer = 'Нет саундтрека'
        elif question.question_type == QuestionType.PHOTO:
            answer = 'Нет фото'
        else:
            raise AssertionError from exc
    else:
        if question.question_type in (QuestionType.TEXT, QuestionType.DIGITS):
            pass
        elif question.question_type == QuestionType.AUDIO:
            if answer[0]:
                show = True
                answer = 'Добавлено аудио'
            else:
                answer = answer[1]
        elif question.question_type == QuestionType.PHOTO:
            show = True
            answer = f'Добавлено {len(answer)} фото'
        else:
            raise AssertionError
        remove = True

    chat_data.print_messages(
        {'text': _format_question_text(question), 'parse_mode': 'MarkdownV2'},
        {'text': answer, 'reply_markup': _question_keyboard(show, remove)}
    )
    return ASK_QUESTION

def _proc_answer(update: Update, context: CallbackContext):
    user_data = UserData.from_context(context)
    chat_data = ChatData.from_context(context)
    question = user_data.questions[user_data.current_question]

    if question.question_type == QuestionType.PHOTO:
        queue = context.dispatcher.update_queue

        updates = [update]
        for _ in range(queue.qsize()):
            updates.append(queue.get())
        data = [update.message for update in updates]
    else:
        data = update.message

    try:
        user_data.answers = (question.tag, data)
        user_data.current_question += 1
        return _ask_question(update, context)
    except AnswerError as exc:
        chat_data.print_error(str(exc))
        return ASK_QUESTION

def _show_form(update: Update, context: CallbackContext):
    chat_data = ChatData.from_context(context)
    user_data = UserData.from_context(context)

    chat_data.send_form(user_data, callback_data=str(REMOVE))
    update.callback_query.answer()
    return SELECT_ACTION

def _back(update: Update, context: CallbackContext) -> None:
    user_data = UserData.from_context(context)
    if user_data.back:
        logger.debug(f'returning back: {user_data.back}')
        return user_data.back(update, context)
    return _select_level(update, context)

def _remove(update: Update, context: CallbackContext):
    chat_data = ChatData.from_context(context)
    chat_data.delete_form(chat_data.id)
    update.callback_query.answer()

def _update_chat(update: Update, context: CallbackContext):
    try:
        ChatData.from_context(context).needs_update = True
    except MissingDataError:
        ChatData(update.message.chat).update_context(context)

def new_status(var_id: int):
    """Send an update message to user."""
    try:
        data = ChatData.by_id(var_id)
    except MissingDataError:
        return

    keyboard = InlineKeyboardMarkup.from_button(InlineKeyboardButton(
        text='Посмотреть', callback_data=str(MANAGE_FORM)
    ))

    # Send user a notification
    data.needs_update = True
    data.print_messages(
        {'text': 'Статус анкеты изменился.', 'reply_markup': keyboard}
    )

def add_handlers(dispatcher: Dispatcher) -> None:
    """Add handlers for private conversation."""
    select_level_handlers = [
        CallbackQueryHandler(_show_help, pattern=f'^{SHOW_HELP}$'),
    ]

    select_action_handlers = [
        CallbackQueryHandler(_send_form, pattern=f'^{SEND_FORM}$'),
        CallbackQueryHandler(_withdraw_form, pattern=f'^{WITHDRAW_FORM}$'),
        CallbackQueryHandler(_delete_form, pattern=f'^{DELETE_FORM}$'),
        CallbackQueryHandler(_ask_question, pattern=f'^{ASK_QUESTION}$'),
        CallbackQueryHandler(_show_form, pattern=f'^{SHOW_FORM}$'),
    ]

    answer_question_handlers = [
        CallbackQueryHandler(_shift_question, pattern=f'^{PREV_QUESTION}$|^{NEXT_QUESTION}$'),
        CallbackQueryHandler(_delete_answer, pattern=f'^{DELETE_ANSWER}$'),
        CallbackQueryHandler(_show_media, pattern=f'^{SHOW_FILE}$'),
        MessageHandler(Filters.all & (~Filters.command), _proc_answer),
    ]

    fallback_handlers = [
        CallbackQueryHandler(_manage_form, pattern=f'^{MANAGE_FORM}$'),
        CommandHandler('stop', _stop, filters=Filters.chat_type.private),
        CallbackQueryHandler(_back, pattern=f'^{BACK}$'),
        CallbackQueryHandler(_remove, pattern=f'^{REMOVE}$'),
    ]

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', _start, filters=Filters.chat_type.private)],
        states={
            SELECT_LEVEL: select_level_handlers,
            SELECT_ACTION: select_action_handlers,
            ASK_QUESTION: answer_question_handlers,
        },
        fallbacks=fallback_handlers,
        name='user',
        persistent=True,
        per_chat=False
    )

    dispatcher.add_handler(MessageHandler(Filters.all, _update_chat), PRIVATE_GROUP)
    dispatcher.add_handler(conv_handler, PRIVATE_GROUP + 1)
