import yaml
import configparser
import logging
import os
import argparse

from yaml import load, dump
from telegram.ext import Updater

from yamlpersistence import YamlPersistence

logger = logging.getLogger(__name__)

def parse_config(path: os.path) -> Updater:
    if os.path.exists(path):
        config = configparser.ConfigParser()
        config.read(path)

        #TODO: exception
        if 'token' in config['Bot']:
            token = config['Bot']['token']
            logger.info("Bot token is: " + token) 

            directory = config['Common']['db_dir']
            my_persistence = YamlPersistence(directory)

            return Updater(token, persistence=my_persistence, use_context=True)
        else:
            #TODO: handle this
            logger.info("Couldn't parse config")
            return nill 

def parse_arg() -> None:
    parser = argparse.ArgumentParser(description='Polydating bot daemon.')
    parser.add_argument('-t', '--token', metavar='token',
                        help='bot token')
    parser.parse_args()

def parse_form():
    return yaml.load(open('config/dating-form.yaml', 'r'))
