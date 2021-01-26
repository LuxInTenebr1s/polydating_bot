import logging
from os import (
    path,
    curdir,
    listdir,
)
from typing import Dict, AnyStr, Mapping, Any

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from argparse import (
    ArgumentParser,
    ArgumentError,
    ArgumentTypeError,
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
        config = self.__parse_args()
        if 'config_dir' in config:
            self.config_dir
        config = self.__parse_config('')

    def update(self):

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
        with open(path.join(pathname, filename)) as file:
            try:
                return yaml.load(file, Loader=Loader)['Common']
            except yaml.YAMLError as exc:
                error = f"{'exc.problem_mark'}" if hasattr(exc, 'problem_mark') else ''
                raise TypeError((f"Error in config \'{filename}\'.\n",
                                 f"{error}",)) from exc

    @classmethod
    def __parse_args(cls) -> Dict:
        parser = ArgumentParser(description='PolyDating bot daemon.')

        parser.add_argument('-c', '--config-dir', dest='config_dir', metavar='path',
                            help=f'specify path to config files [{cls.config_dir}]')

        parser.add_argument('-p', '--persist-dir', dest='persist_dir', metavar='path',
                            help=f'specify path to store bot data [{cls.persist_dir}]')

        group = parser.add_mutually_exclusive_group()
        group.add_argument('-t', '--token',  metavar='file', dest='token',
                            type=cls.__open_token, help='bot token filename')

        group.add_argument('token', required=False, dest='token', help='token string')

        parser.add_argument('--log-level', metavar='log', dest='loglevel',
                            choices=['critical', 'error', 'warning', 'info', 'debug'],
                            help='log verbosity level [warning]')
        try:
            return parser.parse_args()
        except ArgumentError as exc:
            raise TypeError((f"Incorrect arguments. See help.\n\n",
                             f"{'ArgumentParser.print_help()'}",)) from exc
        except ArgumentTypeError as exc:
            raise TypeError(f'types failed') from exc
