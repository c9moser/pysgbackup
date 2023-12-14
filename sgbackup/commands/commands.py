# -*- coding: utf-8 -*-
#
# Author: Christian Moser
# License: GPL
# File: sgbackup/commands/commands.py
# Module: sgbackup.commands.commands

from ..command import Command,CommandOptions_None
import getopt
from .. import error
from ..help import get_builtin_help

class ListCommands(Command):
    def __init__(self,app):
        Command.__init__(self,app,'list-commands','List available commands.')

    def get_synopsis(self, command=None):
        if command is None:
            command = self.id
        return "sgbackup {command}".format(command=command)
    
    def get_help(self,command=None):
        if command is None:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)
        
    def parse_vfunc(self,cmd,argv):
        options = CommandOptions_None(self.application,None)
        try:
            opts,args = getopt.getopt(argv,'',[])
        except getopt.GetoptError as err:
            raise error.OptionError("Command \"{command}\" does not take any options!".fomrat(command=cmd))
        
        if (len(args) > 0):
            raise error.OptionError("Command \"{command}\" does not take any arguments!".fomrat(command=cmd))
        
        return options
    
    def execute_vfunc(self,options:CommandOptions_None):
        commands = self.application.commands.list
        cmd_len = 0
        for i in commands:
            if len(i) > cmd_len:
                cmd_len = len(i)

        cmd_len= (((cmd_len // 4) + 1) * 4)
        for i in commands:
            cmd = self.application.commands.get(i)
            print("{}{}{}".format(i,' ' * (cmd_len - len(i)),cmd.description))
        return 0

class ListCommandKeys(Command):
    def __init__(self,app):
        Command.__init__(self,app,'list-command-keys','List command ids')
    

    def get_synopsis(self, command=None):
        if command is None:
            command = self.id

        return "sgbackup {command}".format(command=command)
    
    def get_help(self,command=None):
        if command is None:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)

    def parse_vfunc(self,cmd,argv):
        options = CommandOptions_None(self.application,None)
        try:
            opts,args = getopt.getopt(argv,'',[])
        except getopt.GetoptError as err:
            raise error.OptionError("Command \"{command}\" does not take any options!".fomrat(command=cmd))
        
        if (len(args) > 0):
            raise error.OptionError("Command \"{command}\" does not take any arguments!".fomrat(command=cmd))
        
        return options
    
    def execute_vfunc(self,options:CommandOptions_None):
        for i in self.application.commands.list:
            print(i)
        return 0
    
COMMANDS=[
    (ListCommands,['commands']),
    (ListCommandKeys,['command-keys'])
]
