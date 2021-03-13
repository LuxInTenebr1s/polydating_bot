#!/usr/bin/env python3
"""Main module."""

import logging

from telegram import (
    utils
)
from telegram.ext import (
    Updater,
)

from polydating_bot import (
     MissingDataError
)
from polydating_bot.store import (
    YamlPersistence,
    BotConfig as config
)
from polydating_bot.data import (
    BotData,
    Data,
    Form
)
import polydating_bot.handlers

# Update config file class, i.e. parse cmdline and config directory
config.update()

# Set basic config for logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=config.loglevel,
)

logger = logging.getLogger(__name__)

# Update form questions list (after logger initialization)
Form.load_questions(YamlPersistence.load_file(config.form_file))

def _main():
    persistence = YamlPersistence(directory=config.persist_dir)
    updater = Updater(config.token, persistence=persistence)

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
