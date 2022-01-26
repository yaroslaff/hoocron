#!/usr/bin/env python3

from setuptools import setup
import os
import sys



def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='hoocron',
    version='0.0.4',
    packages=['hoocron_plugin', 'hoocron_plugin.cron', 'hoocron_plugin.http', 'hoocron_plugin.tick'],
    scripts=['bin/hoocron.py'],

    install_requires=['requests'],

    url='https://github.com/yaroslaff/hoocron',
    license='MIT',
    author='Yaroslav Polyakov',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    author_email='yaroslaff@gmail.com',
    description='Cron with hooks (webhook and others)',

    python_requires='>=3',
    classifiers=[
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Pick your license as you wish (should match "license" above)
         'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.4',
    ],
)
