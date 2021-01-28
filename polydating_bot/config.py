import logging
from os import (
    path,
    curdir,
    listdir,
)
from typing import Dict, AnyStr, Mapping, Any

from configparser import ConfigParser
from argparse import (
    ArgumentParser,
    ArgumentError,
    ArgumentTypeError,
    Namespace,
)

import helpers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

#TODO: fix those variables
ROOT = f"{path.expanduser('~/git/pets/polydating-bot')}"
DEFAULT_CONFIG_DIR = f"{path.join(ROOT, 'config')}"
DEFAULT_PERSIST_DIR = f"{path.join(ROOT, 'tmp')}"

class BotConfigMeta(type):
    def __init__(cls, *args, **kwargs):
        cls.__config_dir: str = DEFAULT_CONFIG_DIR
        cls.__persist_dir: str = DEFAULT_PERSIST_DIR
        cls.__loglevel: int = logging.WARNING
        cls.__token: str = str()

    @property
    def token(cls) -> str:
        return cls.__token

    @token.setter
    def token(cls, value: str) -> None:
        if cls.__token or not value:
            return
        cls.__token = value

    @property
    def config_dir(cls) -> str:
        return cls.__config_dir

    @config_dir.setter
    def config_dir(cls, value: str) -> None:
        value = path.normpath(value)
        if path.exists(value):
            cls.__config_dir = value
        else:
            logger.error((f'Couldn\'t find configuration directory: {value}\n',
                          f'Switching to default directory: {cls.__config_dir}',))

    @property
    def persist_dir(cls) -> str:
        return cls.__persist_dir

    @persist_dir.setter
    def persist_dir(cls, value: str) -> None:
        value = path.normpath(value)
        if path.exists(value):
            cls.__config_dir = value
        else:
            logger.error((f'Couldn\'t find persistence directory: {value}\n',
                          f'Switching to default directory: {cls.__persist_dir}',))

    @property
    def loglevel(cls) -> int:
        return cls.__loglevel

    @loglevel.setter
    def loglevel(cls, value: str) -> None:
        level = getattr(logging, value.upper())
        if isinstance(level, int):
            cls.__loglevel = level

class BotConfig(metaclass=BotConfigMeta):
    def __init__(self):
        cls = self.__class__
        args = helpers.dict_strip(vars(cls.__parse_args()))

        config_dir = args.get('config_dir')
        if config_dir:
            cls.config_dir = config_dir

        config = helpers.dict_strip(cls.__parse_config(cls.config_dir))
        logger.info(f'{args}\n{config}')
        args.update(config)

        cls.__update(args)

    @classmethod
    def __update(cls, conf: Dict[str, Any]) -> None:
        for key, val in conf.items():
            if not hasattr(cls.__class__, f'{key}'):
                logger.warn(f'Incorrect config option: {key} = {val}')
                continue
            attr = helpers.get_property_object(cls.__class__, key)
            attr.__set__(cls, val)

    @classmethod
    def __open_token(cls, filename: str) -> str:
        try:
            with open(filename, 'r') as file:
                return file.read()
        except OSError as exc:
            raise TypeError(f'Incorrect token filename: {filename}') from exc

    @classmethod
    def __parse_config(cls, pathname: str) -> Dict:
        for filename in listdir(pathname):
            if filename.endswith('.ini'):
                break

        config = ConfigParser(allow_no_value=True)
        config.read(path.join(pathname, filename))
        config = config._sections

        if 'Common' in config:
            return config['Common']
        else:
            return {}

    @classmethod
    def __parse_args(cls) -> Namespace:
        parser = ArgumentParser(description='PolyDating bot daemon.')

        parser.add_argument('-c', '--config-dir', dest='config_dir', metavar='path',
                            help=f'specify path to config files [{cls.config_dir}]')

        parser.add_argument('-p', '--persist-dir', dest='persist_dir', metavar='path',
                            help=f'specify path to store bot data [{cls.persist_dir}]')

        group = parser.add_mutually_exclusive_group()
        group.add_argument('-t', '--token',  metavar='file', dest='token',
                            type=cls.__open_token, help='bot token filename')

        group.add_argument('token', nargs='?', help='token string')

        parser.add_argument('--log-level', metavar='log', dest='loglevel',
                            choices=['critical', 'error', 'warning', 'info', 'debug'],
                            help='log verbosity level [warning]')
        try:
            args = parser.parse_args()
            if args:
                return args
            else:
                return {}
        except ArgumentError as exc:
            raise TypeError((f"Incorrect arguments. See help.\n\n",
                             f"{'ArgumentParser.print_help()'}",)) from exc
        except ArgumentTypeError as exc:
            raise TypeError(f'types failed') from exc
