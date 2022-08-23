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

import os
import sys

from .. import config
import importlib

from . _plugin import Plugin
from . _loader import PluginLoader

PLUGINS={}

def _check_user_plugins_version():
    if not os.path.isfile(os.path.join(config.CONFIG['user-plugins-dir'],'version')):
        return False
        
    with open(os.path.join(config.CONFIG['user-plugins-dir'],'version'), 'r') as f:
        version_string = f.read()
        
    ck_version = version_string.split('.')
    version = config.CONFIG['version']
    
    if (ck_version[0] == version[0] and ck_version[1] == version[1] and ck_version[2] >= version[2]):
        return True
    return False
# _check_user_plugin_version()

def _is_package(path):
    if os.path.isdir(path) and os.path.isfile(os.path.join(path,'__init__.py')):
        return True
    return False

if config.CONFIG['user-plugins-enabled']:
    if not os.path.isdir(config.CONFIG['user-plugins-dir']):
        os.makedirs(config.CONFIG['user-plugins-dir'])
        with open(os.path.join(os.path.dirname(__file__),'_user_plugins_init.py'), 'r') as ifile:
            s = ifile.read()
        with open(os.path.join(config.CONFIG['user-plugins-dir'],'__init__.py'), 'w') as ofile:
            ofile.write(s)
        with open(os.path.join(config.CONFIG['user-plugins-dir'],'version'),'w') as ofile:
            ofile.write('.'.join((str(i) for i in config.CONFIG['version'])))
    elif not _check_user_plugins_version():
        with open(os.path.join(os.path.dirname(__file__),'_user_plugins_init.py'),'r') as ifile:
            s = ifile.read()
        with open(os.path.join(config.CONFIG['user-plugins-dir'],'__init__.py'), 'w') as ofile:
            ofile.write(s)
        with open(os.path.join(config.CONFIG['user-plugins-dir'],'version'),'w') as ofile:
            ofile.write('.'.join((str(i) for i in config.CONFIG['version'])))
            
loader = PluginLoader()
for i in os.listdir(os.path.dirname(__file__)):
    if i.startswith('.') or i.startswith('_'):
        continue
        
    module = None
    if i.endswith('.py'):
        m = i[:-3]
        #module = importlib.import_module('.' + m,__package__)
        try:
            module = importlib.import_module('.' + m,__package__)
        except ImportError as error:
            print('Unable to import plugin-module "{0}"! ({1})'.format(m,error),file=sys.stderr)
            continue        
        
        try:
            exec("{0}=module".format(m))
        except Exception as error:
            print('Unable to add module "{0}" to sgbackup.plugins! ({1})'.format(m,error),file=sys.stderr)
        
    elif _is_package(os.path.join(os.path.dirname(__file__),i)):
        try:
            module = importlib.import_module('.' + i,__package__)
        except ImportError as error:
            print('Unable to import plugin-package "{0}"! ({1})'.format(i,error),file=sys.stderr)
            continue
        
        try:
            exec("{0}=module".format(i))
        except Exception as error:
            print('Unable to add package "{0}" to sgbackup.plugins! ({1})'.format(i,error),file=sys.stderr)
        
    if module:
        plugin = loader.load(module)
        if (plugin):
            PLUGINS[plugin.name] = plugin
            
if config.CONFIG['user-plugins-enabled']:
    try:
        import sgbackup_plugins
    except ImportError as error:
        print('Unable to import user plugins! ({0})'.format(error),file=sys.stderr)

def get_plugins():
    return sorted(PLUGINS.keys())
    
def enable_plugin(plugin):
    if isinstance(plugin,Plugin):
        plguin.enable()
    else:
        PLUGINS[plugin].enable()
        
def disable_plugin(plugin):
    if isinstance(plugin,Plugin):
        plugin.disable()
    else:
        PLUGINS[plugin].disable()
        
def init_plugins(db):
    for spec in db.list_plugins():
        if spec['enabled']:
            enable_plugin(spec['name'])

    
