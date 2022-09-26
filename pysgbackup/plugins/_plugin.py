#-*- coding:utf-8 -*-
################################################################################
# pysgbackup.plugins
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

from .. import settings
from gi.repository import Gio,Gtk,GObject
import pysgbackup

class Plugin(GObject.GObject):
    __gsignals__ = {
        'enable': (GObject.SIGNAL_RUN_FIRST,None,(pysgbackup.AppWindow))
        'disable': (GObject.SIGNAL_RUN_FIRST,None,(pysgbackup.AppWindow))
    }
    def __init__(self,name,
                 sgbackup_plugin=None,
                 settings=None,
                 menu=None,
                 gameview_menu=None,
                 backupview_menu=None,
                 enable_callback=None,
                 disable_callback=None):
        object.__init__(self)
        
        self.__name = name
        self.__sgbackup_plugin = sgbackup_plugin
        self.__enabled = False
        self.__settings = settings
        self.__menu = menu
        self.__gameview_menu = backupview_menu
        self.__backupview_menu = gameview_menu
        self.__enable_cb = enable_callback
        self.__disable_cb = disable_callback
        
    @staticmethod
    def new_from_dict(self,d):
        if 'name' in d:
            name = d['name']
            sgbackup_plugin = None
            settings = None
            menu = None
            gameview_menu = None
            backupview_menu = None
            enable_cb = None
            disable_cb = None
            
            return Plugin(name,
                          sgbackup_plugin = sgbackup_plugin,
                          settings = settings,
                          menu = menu,
                          gameview_menu = gameview_menu,
                          backupview_menu = backupview_menu,
                          enable_callback = enable_cb,
                          disable_callback = disable_cb)
                
        return None
            
    @GObject.Property
    def name(self):
        return self.__name
        
    @GObject.Property
    def enabled(self):
        return self.__enabled = False
            
    @GObject.Property
    def sgbackup_plugin(self):
        return self.__sgbackup_plugin
        
    @GObject.Property
    def settings(self):
        return self.__settings
        
    @GObject.Property
    def menu(self):
        return self.__menu
    
    @GObject.Property
    def gameview_menu(self):
        return self.__gameview_menu
        
    @GObject.Property
    def backupview_menu(self):
        return self.__backupview_menu
        
    def enable(self,appwindow):
        self.emit('enable',appwindow)
        
    def disable(self,appwindow):
        self.emit('disable',appwindow)
        
    def do_enable(self,appwindow):
        if self.__enable_cb and callable(self.__enable_cb):
            self.__enable_cb(self,appwindow)
        
    def do_disable(self,appwindow):
        if self.__disable_cb and callable(self.__disable_cb):
            self.__disable_cb(self,appwindow)
# Plugin class

class Loader(object):
    def __init__(self):
        object.__init__(self)
        
    def load(self,module):
        if hasattr(module,'plugin'):
            if isinstance(module.plugin,Plugin):
                return module.plugin
            elif isinstance(module.plugin,dict) and 'name' in dict:
                return Plugin.new_from_dict(module.plugin)
        return None
# Loader class
