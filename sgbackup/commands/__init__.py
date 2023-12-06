# -*- coding: utf-8 -*-

# Author: Christian Moser
# License: GPL
# File: sgbackup/commands/__init__.py
# Module sgbackup.commands

import os

BUILTIN_COMMANDS=[]
BUILTIN_COMMANDS_DIR = os.path.dirname(__file__)
_mods=[]
for i in os.listdir(BUILTIN_COMMANDS_DIR):
    fname = os.path.join(BUILTIN_COMMANDS_DIR)
    if (i.startswith('.') or i.startswith('_')):
        continue
    elif (i.endswith('.py')):
        m = i[:-3]
        if m in _mods:
            continue
        _mods.append(m)
    elif (i.endswith('.pyc')):
        m = i[:-4]
        if m in _mods:
            continue
        _mods.append(m)
    elif (os.path.isdir(fname) 
          and (os.path.isfile(os.path.join(fname,'__init__.py')) or os.path.isfile(os.path.join(fname,'__init__.pyc')))):
        m = i
        if m in _mods:
            continue
        _mods.append(m)

for m in _mods:
    exec("""from . import {module}
if hasattr({module},"COMMANDS"):
    for command in {module}.COMMANDS:
        BUILTIN_COMMANDS.append(command)
""".format(module=m))
del _mods
  
