#!/usr/bin/env python

from setuptools import setup

exec(open("erc20token/version.py").read())

with open('requirements.txt') as f:
    requires = [line.strip() for line in f if line.strip()]
with open('requirements-dev.txt') as f:
    tests_requires = [line.strip() for line in f if line.strip()]

setup(
    name='erc20token',
    version=__version__,
    description='ERC20 token SDK for Python',
    author='Kin Foundation',
    maintainer='David Bolshoy',
    maintainer_email='david.bolshoy@kik.com',
    url='https://github.com/kinfoundation/erc20token-sdk-python',
    license='GPLv2',
    packages=["erc20token"],
    long_description=open("README.md").read(),
    keywords = ["ethereum", "erc20", "blockchain", "cryptocurrency"],
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Intended Audience :: Developers',
        'Development Status :: 4 - Beta',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
    install_requires=requires,
    tests_require=tests_requires,
)
