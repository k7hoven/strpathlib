#!/usr/bin/env python

"""Setup script for np."""

import setuptools
import os

with open('README.rst') as f:
    README = f.read()

with open('proposal.rst') as f:
    CHANGES = f.read()
    
with open('requirements.txt') as f:
    REQUIREMENTS = f.readlines()

setuptools.setup(
    name="strpathlib",
    version='0.1.0',
    description="a fork of Python's stdlib module pathlib with str inheritance",
    url='https://github.com/k7hoven/strpathlib',
    author='This fork: Koos Zevenhoven',
    author_email='koos.zevenhoven@aalto.fi',
    packages=setuptools.find_packages(exclude = ('tests',)),
    long_description=(README + '\n' + CHANGES),
    license='See LICENSE file',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires = REQUIREMENTS,
)

