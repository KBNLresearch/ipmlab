#!/usr/bin/env python
"""Setup script for Ipmlab"""

import codecs
import os
import re
from setuptools import setup, find_packages


def read(*parts):
    """Read file and return contents"""
    path = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(path, encoding='utf-8') as fobj:
        return fobj.read()


def find_version(*file_paths):
    """Return version number from main module"""
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


INSTALL_REQUIRES = [
    'requests',
    'setuptools',
    'lxml'
]
PYTHON_REQUIRES = '>=3.2'

setup(name='ipmlab',
      packages=find_packages(),
      version=find_version('ipmlab', 'ipmlab.py'),
      license='Apache License 2.0',
      install_requires=INSTALL_REQUIRES,
      python_requires=PYTHON_REQUIRES,
      platforms=['Windows'],
      description='Image Portable Media Like A Boss',
      long_description='Workflow software for automated imaging of portable storage media',
      author='Johan van der Knijff',
      author_email='johan.vanderknijff@kb.nl',
      maintainer='Johan van der Knijff',
      maintainer_email='johan.vanderknijff@kb.nl',
      url='https://github.com/KBNLresearch/ipmlab',
      download_url=('https://github.com/KBNLresearch/ipmlab/archive/' +
                    find_version('ipmlab', 'ipmlab.py') + '.tar.gz'),
      package_data={'ipmlab': ['*.*', 'conf/*.*']},
      zip_safe=False,
      entry_points={'gui_scripts': [
          'ipmlab = ipmlab.ipmlab:main',
          'ipmlab-configure = ipmlab.configure:main',
      ]},
      classifiers=[
          'Programming Language :: Python :: 3',]
     )
