#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
from distutils.core import setup

scripts = []
for base in os.listdir('scripts'):
    if base == '.svn':
        continue
    if base.endswith('~'):
        continue
    if base.endswith('.bak'):
        continue
    if base.endswith('.swp'):
        continue
    scripts.append('scripts/%s' % base)

setup(name='etc', version='0.1',
      description="Collection de modules Python d'intérêt commun.",
      author='François Pinard',
      author_email='pinard@iro.umontreal.ca',
      url='http://www.iro.umontreal.ca/~pinard',
      scripts=scripts,
      packages=['Etc', 'Etc.Allout', 'Etc.NoSpam', 'Etc.NoSpam.DNS'])
