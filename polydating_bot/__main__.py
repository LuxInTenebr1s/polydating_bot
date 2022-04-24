#!/usr/bin/env python3
"""Main module."""

import logging

from dynaconf import (
    settings
)

from telegram import (
    utils
)

from telegram.ext import (
    Updater,
)

from polydating_bot import (
     MissingDataError,
     PersistenceError
)

from polydating_bot.store import (
    YamlPersistence
)
from polydating_bot.data import (
    BotData,
    Data,
    Form
)
import polydating_bot.handlers

logger = logging.getLogger(__name__)

def _setup_logger() -> None:
    try:
        log_level = getattr(logging, settings.LOG_LEVEL.upper())
    except (ValueError, AttributeError):
        log_level = logging.INFO # pylint: disable=C0103
    finally:
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=log_level,
        )

def _load_form_file() -> None:
    try:
        Form.load_questions(YamlPersistence.load_file(settings.FORM_FILE))
    except AttributeError as exc:
        raise PersistenceError("Specify path to form file") from exc
    except TypeError as exc:
        raise PermissionError("Incorrect form file format") from exc

def _main():
    # Setup logger based on settings file
    _setup_logger()

    # Load form file with questions for bot
    _load_form_file()

    persistence = YamlPersistence(directory=settings.PERSIST_DIR)
    updater = Updater(settings.TOKEN, persistence=persistence)

    dispatcher = updater.dispatcher
    logger.info('Dispatcher is created.')

    # Create bot data if missing
    try:
        bot_data = BotData.from_dict(dispatcher.bot_data)
    except MissingDataError:
        bot_data = BotData()
        bot_data.update_dict(dispatcher.bot_data)

    # Generate deep-linked URL to link owner to the bot; printed via logs
    uname = dispatcher.bot.getMe().username
    url = utils.helpers.create_deep_linked_url(uname, bot_data.uuid, False)
    logger.info(f'User link: {url}')
    url = utils.helpers.create_deep_linked_url(uname, bot_data.uuid, True)
    logger.info(f'Group link: {url}')

    # Update persistence data
    Data.update_bot(dispatcher.bot)

    # Register bot handlers, e.g. converstaion/command handlers
    polydating_bot.handlers.add_handlers(dispatcher)

    # Start bot  polling mode
    updater.start_polling()

    # Push updater to another thread
    updater.idle()

if __name__ == '__main__':
    _main()
