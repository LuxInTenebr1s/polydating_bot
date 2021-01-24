from typing import Dict
from os import path, curdir

import yaml
from argparse import ArgumentParser, FileType, ArgumentError, ArgumentTypeError

DEFAULT_DIR = f"{curdir.join('config')}"

def open_token(filename: str) -> str:
    try:
        with open(filename, 'r') as file:
            return file.read()
    except OSError as exc:
        raise TypeError(f'Incorrect token filename: ${filename}') from exc

class BotConfig:
    def __init__(self):
        pass

    def parse_config(self, path: str) -> Dict:


    def parse_args(self) -> Dict:
        parser = ArgumentParser(description='PolyDating bot daemon.')

        parser.add_argument('-c', '--config', type=path.abspath,
                            default=DEFAULT_DIR, metavar='path',
                            help=f'specify path to config files [{DEFAULT_DIR}]')

        group = parser.add_mutually_exclusive_group()
        group.add_argument('-t', '--token', type=open_token, metavar='file',
                            dest='token', help='bot token filename')

        group.add_argument('token', type=str, required=False,
                            help='token string')

        parser.add_argument('-v', '--verbose', action='count', default=0,
                            dest='verbose', help='verbosity level')
        try:
            return parser.parse_args()
        except ArgumentError as exc:
            raise TypeError((f"Incorrect arguments. See help.\n\n",
                             f"{'ArgumentParser.print_help()'}",)) from exc
        except ArgumentTypeError as exc:
            raise TypeError(f'types failed') from exc


