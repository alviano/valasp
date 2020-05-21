#!/usr/bin/env python

from distutils.core import setup
from valasp import __version__

setup(
    name='valasp',
    version=__version__,
    description='Validation framework for Answer Set Programming',
    author='Mario Alviano, Carmine Dodaro',
    author_email='mario.alviano@gmail.com, carmine.dodaro@gmail.com',
    url='https://github.com/alviano/valasp',
    packages=['valasp'],
)
