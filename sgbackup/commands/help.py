# -*- coding : utf-8 -*-

# Author: Christian Moser
# License: GPL
# File: sgbackup/commands/help.py
# Module: sgbackup.commands.help

from ..command import Command,CommandOptions
from .. import error
from ..help import get_builtin_help,create_help_title
import getopt
import sys
import subprocess

class SynopsisOptions(CommandOptions):
    OPTION_ID = "command-synopsis"

    def __init__(self,app,command):
        CommandOptions.__init__(self,app,self.OPTION_ID,command)
        self.__topic = None

    @property
    def topic(self):
        return self.__topic
    
    @topic.setter
    def topic(self,topic:str):
        if not self.application.commands.has_command(topic):
            raise ValueError("No such command \"{}\"!".format(topic))
        self.__topic = topic
 
class Synopsis(Command):
    def __init__(self,app):
        Command.__init__(self,app,'synopsis','Print usage information.')

    def get_sgbackup_synopsis(self):
        return "sgbackup [-vV] <COMMAND> [OPTIONS] [ARGS]"
    
    def get_synopsis(self,command=None):
        if command is None:
            command = 'synopsis'
        return "sgbackup {} [COMMAND]".format(command)
    
    def get_help(self, command=None):
        if command is None:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)

    def parse_vfunc(self, cmd, argv):
        try:
            opts,args = getopt.getopt(argv,'',[],)
        except getopt.GetoptError as err:
            raise error.OptionError(err.msg)
        
        options = SynopsisOptions(self.application,cmd)
        if len(args) > 1:
            raise error.OptionError("\"sgbackup synopsis\" only takes one argument!")
        elif len(args) == 1:
            try:
                options.topic = args[0]
            except LookupError as err:
                raise error.OptionError(err.args[0])
            
        return options

    def execute_vfunc(self,options):
        if not options.topic:
            print(self.get_sgbackup_synopsis())
        else:
            print(self.application.commands.get(options.topic).get_synopsis(options.topic))

        return 0

class HelpOptions(CommandOptions):
    OPTION_ID = "command-help"

    def __init__(self,app,command):
        CommandOptions.__init__(self,app,self.OPTION_ID,command)
        self.__topic = None

    @property
    def topic(self):
        return self.__topic
    
    @topic.setter
    def topic(self,topic:str):
        if not self.application.commands.has_command(topic):
            raise ValueError("No such command \"{}\"!".format(topic))
        self.__topic = topic
    
class Help(Command):
    def __init__(self,app):
        Command.__init__(self,app,'help','Print help messages.')

    def get_synopsis(self,command=None):
        if command is None:
            command = 'help'
        return "sgbackup {} [COMMAND]".format(command)
    
    def get_sgbackup_help(self):
        command=""
        var_commands=""
        command_list = self.application.commands.list
        cmd_len = 0
        for i in command_list:
            x = len(i)
            if x > cmd_len:
                cmd_len = x

        for i in command_list:
            var_commands += ("    {}{}  {}\n".format(i," " * (cmd_len - len(i)),self.application.commands.get(i).description))

        return get_builtin_help(
            'sgbackup',
            command,
            self.application.commands.get('synopsis').get_sgbackup_synopsis(),
            None,
            {
                'COMMANDS':var_commands,
                'PYSGBACKUP_CONFIG':self.application.config.user_config,
                'GAME_DIR':self.application.config.gameconf_dir,
            }) 
    
    def get_help(self,command=None):
        if command is None:
            command = self.id
        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)
    
    def parse_vfunc(self,cmd,argv):
        try:
            opts,args = getopt.getopt(argv,'',[],)
        except getopt.GetoptError as err:
            raise error.OptionError(err.msg)
        
        options = HelpOptions(self.application,cmd)
        if len(args) > 1:
            raise error.OptionError("\"sgbackup synopsis\" only takes one argument!")
        elif len(args) == 1:
            try:
                options.topic = args[0]
            except LookupError as err:
                raise error.OptionError(err.args[0])
            
        return options
    
    def execute_vfunc(self,options):
        if not options.topic:
            text = self.get_sgbackup_help()
        else:
            text = self.application.commands.get(options.topic).get_help(options.topic)

        if sys.stdout.isatty:
            process = subprocess.Popen(self.application.config.pager,stdin=subprocess.PIPE)
            process.stdin.write(text.encode('utf-8'))
            process.communicate()
        else:
            print(text)
        return 0
    
COMMANDS = [
    (Synopsis,['usage']),
    (Help,None)
]
