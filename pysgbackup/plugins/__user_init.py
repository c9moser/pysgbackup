#-*- coding:utf-8 -*-
################################################################################
# pysgbackup_plugins
#   Copyright (C) 2022,  Christian Moser
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
################################################################################

import os,sys
import importlib
from pysgbackup import plugins

PLUGIN_DIR = os.path.dirname(__file__)

for i in os.listdir(PLUGIN_DIR):
    if i.startswith('.') or i.startswith('_'):
        continue
        
    fn = os.path.join(PLUGIN_DIR,i)
    if os.path.isfile(fn) and i.endswith('.py'):
        try:
            m = i[:-3]
            module = importlib.import_module('.' + m,__package__)
            if module:
                exec('{}=module'.format(m))
                if hasattr(module,'plugin'):
                    plugins.load_plugin(module.plugin)
        except Exception as error:
            print(error,file=sys.stderr)
            print(traceback.format_exc(),file=sys.stderr)
    elif os.path.isdir(fn) and os.path.isfile(os.path.join(fn,'__init__.py')):
        try:
            module = importlib.import_module('.' + i,__package__)
            if module:
                exec('{}=module'.format(i))
                if hasattr(module,'plugin'):
                    plugins.load_plugin(module.plugin)
        except Exception as error:
            print(error,file=sys.stderr)
            print(traceback.format_exc(),file=sys.stderr)

