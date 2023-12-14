# -*- coding:utf-8 -*-
# author: Christian Moser
# file: sgbackup/commands/plugin.py
# module: sgbackup.commands.plugin.py
# license: GPL

from ..command import Command,CommandOptions
from ..error import OptionError
import sys

class PluginOptions(CommandOptions):
    PLUGIN_ID = 'plugin'
    PLUGIN_SUBCOMMANDS=["list","enable","disable","status","description"]

    def __init__(self,app,cmd):
        CommandOptions.__init__(self,app,self.PLUGIN_ID,cmd)
        self.__subcommand = "list"
        self.__plugin = ""

    @property
    def subcommand(self):
        return self.__subcommand

    @subcommand.setter
    def subcommand(self,sc:str):
        if sc in self.PLUGIN_SUBCOMMANDS:
            self.__subcommand = sc
            return       
        raise ValueError("Not a valid subcommand!")
    
    @property
    def plugin(self):
        return self.__plugin
    
    @plugin.setter
    def plugin(self,plugin_id:str):
        if plugin_id in self.application.plugins.plugins:
            self.__plugin = plugin_id
            return
        raise LookupError("No such plugin \"{plugin}\"!".format(plugin=plugin_id))
        
    @property
    def is_valid(self):
        if self.subcommand == 'list':
            return True
        if self.plugin:
            return True
        return False

class Plugin(Command):
    def __init__(self,app):
        Command.__init__(self,app,PluginOptions.PLUGIN_ID,'Plugin management')

    def get_synopsis(self, command=None):
        if command is None:
            command = PluginOptions.PLUGIN_ID
        return """{command} [list]
{command} [description|disable|enable|status] PLUGIN""".format(command=command)
        
    def parse_vfunc(self, cmd, argv):
        options = PluginOptions(self.application,cmd)

        if len(argv) > 0:
            try:
                options.subcommand = argv[0]
            except ValueError as err:
                raise OptionError("Illegal subcommand \"{subcommand}\"!".format(subcommand=argv[0]))
            
        if len(argv) > 1:
            try:
                options.plugin = argv[1]
            except LookupError as err:
                raise OptionError("Illegal plugin! ({message})".format(message=err.args[0]))
            
        if len(argv) > 2:
            print("WARNING: Too many arguments! IGNORING!",file=sys.stderr)

        if not options.is_valid:
            raise OptionError("Missing arguments!")
            
        return options
        
    def execute_vfunc(self, options:PluginOptions):
        if not options.is_valid:
            raise OptionError("Invalid options!")
        
        if options.subcommand == "list":
            plugins = self.application.plugins.plugins
            key_len = 0
            for key in plugins.keys():
                if len(key) > key_len:
                    key_len = len(key)

            key_len = (((key_len // 8) + 1) * 8)
            for key in sorted(plugins.keys()):
                print('{}{}{}'.format(key,(" " * (key_len - len(key))),plugins[key].name))
        elif options.subcommand == "description":
            try:
                plugin = self.application.plugins.get(options.plugin)
            except LookupError as err:
                print(err,file=sys.stderr)
                return 1
            print(plugin.description)
        elif options.subcommand == "enable":
            try:
                plugin = self.application.plugins.get(options.plugin)
            except LookupError as err:
                print(err,file=sys.stderr)
                return 1
            plugin.enable()
            if self.application.config.verbose:
                print("{plugin} enabled!".format(plugin=options.plugin))
        elif options.subcommand == "disable":
            try:
                plugin = self.application.plugins.get(options.plugin)
            except LookupError as err:
                print(err,file=sys.stderr)
                return 1
            plugin.disable()
            if self.application.config.verbose:
                print("{plugin} disabled!".format(plugin=options.plugin))
        elif options.subcommand == 'status':
            try:
                plugin = self.application.plugins.get(options.plugin)
            except LookupError as err:
                print(err,file=sys.stderr)
                return 1
            if plugin.is_enabled:
                status = "enabled"
            else:
                status = "disabled"
            print("{plugin} -> {status}".format(plugin=options.plugin,status=status))
            

COMMANDS=[
    (Plugin,None)
]