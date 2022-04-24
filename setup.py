#!/usb/bin/env python3
"""Setup script."""

from setuptools import setup, find_packages

setup(
    name='Polydating bot',
    version='0.1.0',
    description='Telegram bot for dating.',
    author='Lux',
    author_email='sr.Lux1nt@gmail.com',
    url='https://github.com/LuxInTenebr1s/polydating_bot',
    packages=find_packages(),
    package_data={
        'polydating_bot': ['config/*.toml'],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': ['polybot = polydating_bot.__main__:_main']
    },
)
