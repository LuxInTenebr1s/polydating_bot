#!/usr/bin/env python3
"""Config module."""

import logging
import inspect
import os

from typing import (
    Dict,
    Any
)

from configparser import (
    ConfigParser
)
from argparse import (
    Namespace,
    ArgumentParser
)

logger = logging.getLogger(__name__)

#TODO: fix those variables
ROOT = f"{os.path.expanduser('~/git/pets/polydating-bot')}"
DEFAULT_CONFIG_DIR = f"{os.path.join(ROOT, 'config')}"
DEFAULT_PERSIST_DIR = f"{os.path.join(ROOT, 'tmp')}"
QUEST_FORM = 'dating-form.yaml'

def _get_property_object(obj: object, attr: str) -> property:
    """Helpers to get properties of the object."""
    assert not attr.startswith('_')

    obj_list = []
    if inspect.isclass(obj):
        obj_list.extend(obj.__class__.mro(obj))
    else:
        obj_list.append(obj).extend(obj.__class__.mro())

    for i in obj_list:
        if attr in i.__dict__:
            return i.__dict__[attr]
    raise AttributeError(obj)

def _dict_strip(data: Dict) -> Dict:
    """Helper to strip dictionary from items with 'False' values."""
    keys = []
    for key, val in data.items():
        if not val:
            keys.append(key)
    for key in keys:
        del data[key]
    return data

class _BotConfigMeta(type):
    def __init__(cls, *args, **kwargs):
        super().__init__(cls, args, kwargs)

        cls._config_dir: str = DEFAULT_CONFIG_DIR
        cls._persist_dir: str = DEFAULT_PERSIST_DIR
        cls._loglevel: int = logging.WARNING
        cls._token: str = str()

    @property
    def token(cls) -> str:
        """Token value."""
        return cls._token

    @token.setter
    def token(cls, value: str) -> None:
        if cls._token or not value:
            return
        cls._token = value

    @property
    def config_dir(cls) -> str:
        """Configuration files directory."""
        return cls._config_dir

    @config_dir.setter
    def config_dir(cls, value: str) -> None:
        path = str()
        try:
            path = os.path.normpath(value)
            os.mkdir(path)
            cls._config_dir = path
        except OSError:
            logger.error(f'Couldn\'t find configuration directory: {value}')
            logger.info(f'Switching to default directory: {cls._config_dir}')

    @property
    def persist_dir(cls) -> str:
        """Persistence directory."""
        return cls._persist_dir

    @persist_dir.setter
    def persist_dir(cls, value: str) -> None:
        path = os.path.normpath(value)
        if os.path.exists(path):
            cls._persist_dir = value
        else:
            logger.error(f'Couldn\'t find persistence directory: {path}')
            logger.info(f'Switching to default directory: {cls._persist_dir}')

    @property
    def loglevel(cls) -> int:
        """Logging level."""
        return cls._loglevel

    @loglevel.setter
    def loglevel(cls, value: str) -> None:
        level = getattr(logging, value.upper())
        if isinstance(level, int):
            cls._loglevel = level

    @property
    def form_file(cls) -> str:
        """Form questions file."""
        return os.path.join(cls.config_dir, QUEST_FORM)

class BotConfig(metaclass=_BotConfigMeta):
    """Bot configuration class."""

    @classmethod
    def update(cls):
        """Update configuration."""
        args = _dict_strip(vars(cls._parse_args()))

        config_dir = args.get('config_dir')
        if config_dir:
            cls.config_dir = config_dir

        config = _dict_strip(cls._parse_config(cls.config_dir))
        args.update(config)

        cls._update(args)
        if not cls.token:
            raise ValueError('No \'token\' value is provided')

    @classmethod
    def _update(cls, conf: Dict[str, Any]) -> None:
        for key, val in conf.items():
            if not hasattr(cls.__class__, f'{key}'):
                logger.warning(f'Incorrect config option: {key} = {val}')
                continue
            attr = _get_property_object(cls.__class__, key)
            attr.__set__(cls, val)

    @classmethod
    def _open_token(cls, filename: str) -> str:
        try:
            with open(filename, 'r') as file:
                return file.read()
        except OSError as exc:
            raise ValueError(f'Incorrect token filename: {filename}') from exc

    @classmethod
    def _parse_config(cls, pathname: str) -> Dict:
        for filename in os.listdir(pathname):
            if filename.endswith('.ini'):
                break
        filename = next((f for f in os.listdir(pathname) if f.endswith('.ini')))
        config = ConfigParser(allow_no_value=True)
        config.read(os.path.join(pathname, filename))

        try:
            return config['Common']
        except KeyError:
            return {}

    @classmethod
    def _parse_args(cls) -> Namespace:
        parser = ArgumentParser(description='PolyDating bot daemon.')

        parser.add_argument('-c', '--config-dir', dest='config_dir', metavar='path',
                            help=f'specify path to config files [{cls.config_dir}]')

        parser.add_argument('-p', '--persist-dir', dest='persist_dir', metavar='path',
                            help=f'specify path to store bot data [{cls.persist_dir}]')

        group = parser.add_mutually_exclusive_group()
        group.add_argument('-t', '--token',  metavar='file', dest='token',
                            type=cls._open_token, help='bot token filename')

        group.add_argument('token', nargs='?', help='token string')

        parser.add_argument('--log-level', metavar='log', dest='loglevel',
                            choices=['critical', 'error', 'warning', 'info', 'debug'],
                            help='log verbosity level [warning]')
        args = parser.parse_args()
        return args if args else {}
