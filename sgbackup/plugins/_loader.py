#-*- coding:utf-8 -*-
################################################################################
# sgbackup
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

from ._plugin import Plugin

class PluginLoader(object):
    def __init__(self):
        object.__init__(self)
        
    def validate_plugin_dict(self,dict):
        keys=['name']
        for k in keys:
            if not k in dict:
                return False
        return True
        
    def load(self,module):
        if hasattr(module,'plugin'):
            if isinstance(module.plugin,Plugin):
                return module.plugin
            elif isinstance(module.plugin,dict):
                if self.validate_plugin_dict(module.plugin):
                    return Plugin.new_from_dict(module.plugin)
        return None

