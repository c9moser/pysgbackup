# -*- coding: utf-8 -*-
# Author: Chrstian Moser
# License: GPL
# File: sgbackup/plugin.py
# Module: sgbackup.plugin

from gi.repository import GObject
import os
import sys
import importlib

class Plugin(GObject.GObject):
    __name__ = "sgbackup_plugin_Plugin"
    __gsignals__ = {
        'destroy': (GObject.SIGNAL_RUN_FIRST,None,()),
        'enable': (GObject.SIGNAL_RUN_FIRST,None,()),
        'disable': (GObject.SIGNAL_RUN_FIRST,None,()),
    }

    def __init__(self,app,id:str,name:str,description=""):
        GObject.GObject.__init__(self)
        self.__app = app
        self.__id = id
        self.__name = name
        self.__description = description
        self.__is_enabled = False

    @GObject.Property
    def is_initialized(self):
        if self.__app is None:
            return False
        return True

    
    @GObject.Property
    def application(self):
        return self.__app
    
    @GObject.Property
    def id(self):
        return self.__id
    
    @GObject.Property
    def name(self):
        return self.__name
    
    @GObject.Property
    def description(self):
        return self.__description
    
    @GObject.Property
    def is_enabled(self):
        return self.__is_enabled
    
    def enable(self):
        if not self.is_enabled:
            self.emit('enable')
            self.__is_enabled = True
            return True        
        return False

    def disable(self):
        if self.is_enabled:
            self.emit('disable')
            self.__is_enabled = False
            return True
        return False

    def destroy(self):
        self.emit('destroy')

    def do_enable(self):
        pass

    def do_disable(self):
        pass

    def do_destroy(self):
        self.__app = None

class PluginManager(GObject.GObject):
    __name__ = "sgbackup_plugin_PluginManager"
    __gsignals__ = {
        'destroy': (GObject.SIGNAL_RUN_LAST,None,()),
        'enable': (GObject.SIGNAL_RUN_FIRST,None,(Plugin,)),
        'disable': (GObject.SIGNAL_RUN_FIRST,None,(Plugin,)),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.__plugins = {}
      

    @GObject.Property
    def application(self):
        return self.__app
    
    @GObject.Property
    def is_initialized(self):
        return (self.application is not None)


    def _real_initialize(self,app):
        self.__app = app
        self._load_builtin_plugins()
        for i in self.application.config.get_string_list('sgbackup','plugins',[]):
            try:
                self.__plugins[i].enable()
            except:
                pass

    def _load_builtin_plugins(self):
        plugins_dir = os.path.join(os.path.dirname(__file__),'plugins')
        plugins_package = "sgbackup.plugins"

        plugin_mods=[]

        for i in os.listdir(plugins_dir):
            if i.startswith('_') or i.startswith('.'):
                continue
            elif i.endswith('.py'):
                x=i[:-3]
                if x not in plugin_mods:
                    plugin_mods.append(x)
            elif i.endswith('.pyc'):
                x=i[:-4]
                if x not in plugin_mods:
                    plugin_mods.append(x)
            elif os.path.isdir(os.path.join(plugins_dir,i)) and os.path.isfile(os.path.join(plugins_dir,i,'__init__.py')):
                if i not in plugin_mods:
                    plugin_mods.append(i)

        for i in plugin_mods:
            try:
                module = importlib.import_module("." + i,'sgbackup.plugins')
                if hasattr(module,"PLUGIN"):
                    self.add(module.PLUGIN(self.application))

            except ImportError as err:
                print("Importing module '{pakage}.{module} failed! ({message})".format(pakage=plugins_package,module=i,message=err.args[0]),
                      file=sys.stderr)

    @GObject.Property
    def plugins(self):
        return dict(self.__plugins)
    
    def get(self,plugin_id:str):
        try:
            return self.__plugins[plugin_id]
        except:
            raise LookupError("No plugin with id \"{plugin}\" found!".format(plugin=plugin_id))
        
    def add(self,plugin:Plugin):
        if plugin.id in self.__plugins:
            if plugin == self.__plugins[plugin.id]:
                return
            else:
                self.remove(plugin.id)
                
        plugin._pluginmanager_enable_slot = plugin.connect('enable',self.__on_plugin_enable)
        plugin._pluginmanager_disable_slot = plugin.connect('disable',self.__on_plugin_disable)
        self.__plugins[plugin.id] = plugin
                
    def remove(self,plugin_id:str):
        if plugin_id in self.__plugins:
            plugin = self.__plugins[plugin_id]
            if hasattr(plugin,'_pluginmanager_enable_slot'):
                plugin.disconnect(plugin._pluginmanager_enable_slot)
                del plugin._pluginmanager_enable_slot
            if hasattr(plugin,'_pluginmanager_disable_slot'):
                plugin.disconnect(plugin._pluginmanager_disable_slot)
                del plugin._pluginmanager_disable_slot
            plugin.destroy()
            del self.__plugins[plugin_id]


    def destroy(self):
        self.emit('destroy')

    def do_destroy(self):
        for plugin in self.__plugins.values():
            plugin.destroy()
        self.__plugins = {}
        self.__app = None

    def enable(self,plugin):
        if isinstance(plugin,Plugin):
            plugin.enable()
            return
        elif isinstance(plugin,str):
            if plugin not in self.__plugins:
                raise LookupError("Plugin with id \"{plugin}\" not found!".format(plugin=plugin))
            plugin_instance = self.__plugins[plugin]
            plugin_instance.enable()
            return
        raise TypeError("Illegal type for plugin!")

    def disable(self,plugin):
        if isinstance(plugin,Plugin):
            plugin.disable()
            return
        elif isinstance(plugin,str):
            if plugin not in self.__plugins:
                raise LookupError("Plugin with id \"{plugin}\" not found!".format(plugin=plugin))
            plugin_instance = self.__plugins[plugin]
            plugin_instance.disable()
            return
        raise TypeError("Illegal type for plugin!")
        

    def __on_plugin_enable(self,plugin):
        self.emit('enable',plugin)
    
    def __on_plugin_disable(self,plugin):
        self.emit('disable',plugin)

    def do_enable(self,plugin:Plugin):
        enabled_plugins = self.application.config.get_string_list('sgbackup','plugins')
        if plugin.id not in enabled_plugins:
            enabled_plugins.append(plugin.id)
            self.application.config.set_string_list('sgbackup','plugins',enabled_plugins)
            self.application.config.save()

    def do_disable(self,plugin:Plugin):
        enabled_plugins = self.application.config.get_string_list()
        if plugin.id in enabled_plugins:
            for i in range(len(enabled_plugins)):
                if plugin.id == enabled_plugins[i]:
                    del enabled_plugins[i]
                    break
            self.application.config.set_string_list('sgbackup','plugins',enabled_plugins)
            self.application.config.save()
