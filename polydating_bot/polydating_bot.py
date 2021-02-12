#!/usr/bin/env python3
# pylint: disable=W0613, C0116, W1203
# type: ignore[union-attr]
"""Main module."""

import logging

from uuid import (
    uuid4
)

from telegram.ext import (
    Updater
)

from . import (
    yamlpersistence,
    private,
    common,
    public
)
from .data import (
    botdata,
 #   userdata
)
from .config import (
    BotConfig as config
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

def main():
    config.update()
    persistence = yamlpersistence.YamlPersistence(directory=config.persist_dir)

    updater = Updater(config.token, persistence=persistence)
    dispatcher = updater.dispatcher
    logger.info('Dispatcher is created.')

    bot_data = dispatcher.bot_data.get('data')
    if not bot_data:
        bot_data = botdata.BotData(str(uuid4()))
        dispatcher.bot_data['data'] = bot_data
        dispatcher.update_persistence()
    logger.info(f'Current bot UUID: {bot_data.uuid}')

    common.add_handlers(dispatcher)
    private.add_handlers(dispatcher)
    public.add_handlers(dispatcher)

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
