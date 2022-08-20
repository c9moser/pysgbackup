#-*- coding:utf-8 -*-
################################################################################
# sgbackup.plugins
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

import os
import importlib
import sgbackup.plugins


USER_PLUGIN_DIR=os.path.dirname(__file__)

for i in os.listdir(USER_PLUGIN_DIR):
    module = None
    if i.startswith('.') or i.startswith('_'):
        continue
    elif os.path.isfile(os.path.join(USER_PLUGIN_DIR,i)) and i.endswith('.py'):
        m = i[:-3]
        mdoule = importlib.import_module('.' + m,__package__)
        exec('{} = module'.format(m))
        setattr(plugins,m,module)
    elif os.path.isdir(os.path.join(USER_PLUGIN_DIR,i)) and os.path.isfile(os.path.join(USER_PLUGIN_DIR,i,'__init__.py')):
        module = importlib.import_module('.' + i, __package__)
        exec('{} = module'.format(i))
        setattr(plugins,i,module)
        
    if module:
        plugin = plugins.loader.load(module)
        if plugin:
            plugins.PLUGINS[plugin.name] = plugin
# init()

