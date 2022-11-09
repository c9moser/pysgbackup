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

from gi.repository import GObject,Gio,Gtk

import os,sys
import importlib
import traceback
import site
import sgbackup
from ..settings import Settings,SETTINGS
from ..appwindow import AppWindow

PLUGIN_DIR = os.path.dirname(__file__)

if site.ENABLE_USER_SITE:
    ENABLE_USER_PLUGINS = True
    USER_PLUGIN_DIR = os.path.join(site.USER_SITE,'pysgbackup_plugins')
    if not os.path.isdir(USER_PLUGIN_DIR):
        os.makedirs(USER_PLUGIN_DIR)
        with open(os.path.join(os.path.dirname(__file__),'__user_init.py'),'r') as ifile:
            with open(os.path.join(USER_PLUGIN_DIR,'__init__.py'),'w') as ofile:
                ofile.write(ifile.read())
else:
    ENABLE_USER_PLUGINS = False
    USER_PLUGIN_DIR = ''

PLUGINS = {}

class Plugin(GObject.GObject):
    __gsignals__ = {
        'enable': (GObject.SIGNAL_RUN_FIRST,None,(AppWindow,)),
        'disable': (GObject.SIGNAL_RUN_FIRST,None,(AppWindow,))
    }
    
    def __init__(self,name,title,
                 description="",
                 icon=None,
                 version='0.0.0',
                 settings=None,
                 sgbackup_plugin=None,
                 sgbackup_plugin_enable=False,
                 enable_callback=None,
                 disable_callback=None,
                 menu=None,
                 gameview_menu=None,
                 backupview_menu=None):
        GObject.GObject.__init__(self)
        
        self.__name = name
        self.__title = title
        self.__description = description
        self.__version = version
        self.__settings = settings
        self.__enabled = False
        self.__icon = icon
        
        if self.settings:
            SETTINGS[self.settings.id] = settings
                
        if isinstance(sgbackup_plugin,sgbackup.plugins.Plugin):
            self.__sgbackup_plugin = sgbackup_plugin
        elif isinstance(sgbackup_plugin,str):
            if sgbackup_plugin in sgbackup.plugins.PLUGINS:
                self.__sgbackup_plugin = sgbackup.plugins.PLUGINS[sgbackup_plugin]
            else:
                raise LookupError('Sgbackup-plugin "{0}" not found!'.format(sgbackup_plugin))
        elif sgbackup_plugin is None:
            self.__sgbackup_plugin = None
        else:
            raise TypeError('sgbackup_plugin')
            
        if self.__sgbackup_plugin and sgbackup_plugin_enable:
            self.__sgbackup_plugin_enable = True
        else:
            self.__sgbackup_plugin_enable = False            
        
        if enable_callback and callable(enable_callback):
            self.__enable_callback = enable_callback
        else:
            self.__enable_callback = None
            
        if disable_callback and callable(disable_callback):
            self.__disable_callback = disable_callback
        else:
            self.__disable_callback = None
            
        self.__menu = None
        self.__menu_desc = None
        if menu:
            if isinstance(menu,dict) and 'file' in menu and 'object' in menu:
                self.__menu_desc = menu
            elif isinstance(menu,Gio.SimpleMenu):
                self.__menu = menu
        
        self.__gameview_menu = None
        self.__gameview_menu_desc = None
        if gameview_menu:
            if isinstance(gameview_menu,dict) and 'file' in gameview_menu and 'object' in gameview_menu:
                self.__gameview_menu_desc = gameview_menu
            elif isinstance(gameview_menu,Gio.SimpleMenu):
                self.__gameview_menu = gameview_menu
                
        self.__backupview_menu = None
        self.__backupview_menu_desc = None
        if backupview_menu:
            if isinstance(backupview_menu,dict) and 'file' in backupview_menu and 'object' in backupview_menu:
                self.__backupview_menu_desc = backupview_menu
            elif isinstance(backupview_menu,Gio.SimpleMenu):
                self.__backupview_menu = backupview_menu
    # __init__()
        
    @staticmethod
    def new_from_dict(spec):
        if spec['name'] and spec['title']:
            name = spec['name']
            title = spec['title']
            
            kwargs = {}
            if 'sgbackup-plugin' in spec:
                kwargs['sgbackup_plugin'] = spec['sgbackup-plugin']
                if 'sgbackup-plugin-enable' in spec:
                    kwargs['sgbackup_plugin_enable'] = spec['sgbackup-plugin-enable']
            if 'menu' in spec:
                kwargs['menu'] = spec['menu']
            if 'backupview-menu' in spec:
                kwargs['backupview_menu'] = spec['backupview-menu']
            if 'gameview-menu' in spec:
                kwargs['gameview_menu'] = spec['gameview-menu']
            if 'enable-callback' in spec:
                kwargs['enable_callback'] = spec['enable-callback']
            if 'disable-callback' in spec:
                kwargs['disable_callback'] = spec['disable-callback']
                
            return Plugin(name,title,**kwargs)
            
        return None
    # Plugin.new_from_dict()                
        
    @GObject.Property
    def name(self): 
        return self.__name
        
    @GObject.Property
    def title(self):
        return self.__title
        
    @GObject.Property
    def description(self):
        return self.__description
        
    @GObject.Property
    def icon(self):
        return self.__icon
        
    @GObject.Property
    def menu(self):
        return self.__menu
        
    @GObject.Property
    def gameview_menu(self):
        return self.__gameview_menu
        
    @GObject.Property
    def backupview_menu(self):
        return self.__backupview_menu
        
    @GObject.Property
    def sgbackup_plugin(self):
        return self.__sgbackup_plugin
        
    @GObject.Property
    def sgbackup_plugin_enable(self):
        return self.__sgbackup_plugin_enable
        
    @GObject.Property
    def enabled(self):
        if self.sgbackup_plugin and self.sgbackup_plugin_enable:
            return self.sgbackup_plugin.enabled
        return self.__enabled
        
    @GObject.Property
    def settings(self):
        return self.__settings
        
    @GObject.Property
    def version(self):
        return self.__version
        
    def enable(self,appwindow):
        self.emit('enable',appwindow)
        
    def disable(self,appwindow):
        self.emit('disable',appwindow)
        
    def do_enable(self,appwindow):
        builder = Gtk.Builder()
        builder_files = {}
        
        if self.__menu_desc:
            builder_files[self.__menu_desc['file']] = False
        if self.__gameview_menu_desc:
            builder_files[self.__gameview_menu_desc['file']] = False
        if self.__backupview_menu_desc:
            builder_files[self.__backupview_menu_desc['file']] = False
        
        if self.__menu_desc:
            try:
                builder.add_from_file(self.__menu_desc['file'])
                if 'handler' in self.__menu_desc:
                    builder.connect_signals(handler)
                else:
                    builder.connect_signals(self)
                    
                builder_files[self.__menu_desc['file']] = True
                self.__menu = builder.get_object(self.__menu_desc['object'])
            except Exception as error:
                print(error,file=sys.stderr)
        
        if self.__backupview_menu_desc:
            try:
                if not builder_files[self.__backupview_menu_desc['file']]:
                    self.builder.add_from_file(self.__backupview_menu_desc['file'])
                    builder_files[self.__backupview_menu_desc['file']] = True
                    if 'handler' in self.__backupview_menu_desc:
                        self.builder.connect_signals(self.__backupview_menu_desc['handler'])
                    else:
                        self.builder.connect_signals(self)
                        
                self.__backupview_menu = builder.get_object(self.__backupview_menu_desc['object'])
            except Exception as error:
                print(error,file=sys.stderr)
                
        if self.__gameview_menu_desc:
            try:
                if not builder_files[self.__gameview_menu_desc['file']]:
                    self.builder.add_from_file(self.__gameview_menu_desc['file'])
                    builder_files[self.__gameview_menu_desc['file']] = True
                    if 'handler' in self.__backupview_menu_desc:
                        self.builder.connect_signals(self.__backupview_menu_desc['handler'])
                    else:
                        self.builder.connect_signals(self)
                        
                self.__gameview_menu = builder.get_object(self.__gameview_menu_desc['object'])  
            except Exception as error:
                print(error,file=sys.stderr)
        
        if self.menu:
            menuitem = Gio.MenuItem.new_submenu(self.title,self.menu)
            appwindow.appmenu_plugins.append_item(menuitem)
        if self.gameview_menu:
            gameview_menuitem = Gio.MenuItem.new_submenu(self.title,self.gameview_menu)
            appwindow.gameview_popup_plugins.append_item(gameview_menuitem)
        if self.backupview_menu:
            backupview_menuitem = Gio.MenuItem.new_submenu(self.title,self.backupview_menu)
            appwindow.backupview_popup_plugins.append_item(backupview_menuitem)
            
        if self.sgbackup_plugin and self.sgbackup_plugin_enable:
            db = sgbackup.database.Database()
            db.enable_plugin(self.sgbackup_plugin)
            db.close()
            self.sgbackup_plugin.enable()
            
        if self.__enable_callback:
            self.__enable_callback(self,appwindow)
            
        self.__enabled = True
    # Plugin.do_enable()
    
    def do_disable(self,appwindow):
        if self.menu:
            for i in sorted(range(appwindow.appmenu_plugins.get_n_items()),reverse=True):
                attr_label = appwindow.appmenu_plugins.get_item_attribute_value(i,'label',None)
                if attr_label and attr_label.get_string() == self.title:
                    appwindow.appmenu_plugins.remove(i)
        if self.__menu_desc:
            self.__menu = None
            
        if self.gameview_menu:
            for i in sorted(range(appwindow.gameview_popup_plugins.get_n_items()),reverse=True):
                attr_label = appwindow.gameview_popup_plugins.get_item_attribute_value(i,'label',None)
                if attr_label and attr_label.get_string() == self.title:
                    appwindow.gameview_popup_plugins.remove(i)
                    break
        if self.__gameview_menu_desc:
            self.__gameview_menu = None
            
        if self.backupview_menu:
            for i in sorted(range(appwindow.backupview_popup_plugins.get_n_items()),reverse=True):
                attr_label = appwindow.backupview_popup_plugins.get_item_attribute_value(i,'label',None)
                if attr_label and attr_label.get_string() == self.title:
                    appwindow.backupview_popup_plugins.remove(i)
                    break
        if self.__backupview_menu_desc:
            self.__backupview_menu = None
            
        if self.sgbackup_plugin and self.sgbackup_plugin_enable:
            db = sgbackup.database.Database()
            db.disable_plugin(self.sgbackup_plugin)
            db.close()
            self.sgbackup_plugin.disable()
            
        if self.__disable_callback:
            self.__disable_callback(self,appwindow)
            
        self.__enabled = False
    # Plugin.do_disable()
# Plugin class

def load_plugin(plugin):
    if isinstance(plugin,Plugin):
        PLUGINS[plugin.name] = plugin
    elif isinstance(plugin,dict):
        plugin_instance = Plugin.new_from_dict(plugin)
        if plugin_instance:
            PLUGINS[plugin_instance.name] = plugin_instance
# load_plugin()

#BEGIN: Load plugins
for i in os.listdir(PLUGIN_DIR):
    if i.startswith('.') or i.startswith('_'):
        continue
        
    fn = os.path.join(PLUGIN_DIR,i)
    if os.path.isfile(fn) and i.endswith('.py'):
        try:
            m=i[:-3]
            module = importlib.import_module('.' + m,__package__)
            if module:
                exec("{}=module".format(m))
                if hasattr(module,'plugin'):
                    load_plugin(module.plugin)
        except Exception as error:
            print(error,file=sys.stderr)
            print(traceback.format_exc(),file=sys.stderr)
    elif os.path.isdir(fn) and os.path.isfile(os.path.join(fn,'__init__.py')):
        try:
            module = importlib.import_module('.' + i, __package__)
            if module:
                exec("{}=module".format(i))
                if hasattr(module,'plugin'):
                    load_plugin(module.plugin)
        except Exception as error:
            print(error,file=sys.stderr)
            print(traceback.format_exc(),file=sys.stderr)
#END: Load plugins

if ENABLE_USER_PLUGINS:
    try:
        import pysgbackup_plugins as user_plugins
    except Exception as error:
        print(error,file=sys.stderr)
        print(format_exc,file=sys.stderr)

