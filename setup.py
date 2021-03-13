#!/usb/bin/env python3
"""Setup script."""

from distutils.core import setup

setup(
    name='Polydating bot',
    version='0.1.0',
    description='Telegram bot for dating.',
    author='Lux',
    author_email='sr.Lux1nt@gmail.com',
    url='https://github.com/LuxInTenebr1s/polydating_bot',
    packages=[
        'polydating_bot',
        'polydating_bot.data',
        'polydating_bot.store',
        'polydating_bot.handlers'
    ],
)
