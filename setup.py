#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup

__author__ = "Ashish Prasad"
__license__ = "BSD"
__version__ = "1.0"
__email__ = "ashish.ap.rao@gmail.com"
__url__ = ""
__description__ = """Python Mosaics"""
__status__ = "Stable"


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

setup(
    name='PyMos',
    version=__version__,
    author=__author__,
    author_email=__email__,
    url=__url__,
    description=__description__,
    long_description=read('README.md') + "\n\n" + read('CHANGES.txt'),
    license=__license__,
    packages=["pymos"],
    include_package_data=True,
    install_requires=['argparse', 'pillow', 'simplejson'],
    scripts=['bin/pymos'],
)
