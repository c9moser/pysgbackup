# -*- coding: utf-8 -*-

# Author: Christian Moser
# License: GPL
# File: sgbackup/commandmanager.py
# Module: sgbackup.commandmanager

from gi.repository import GObject
from .command import (
    Command,
    CommandOptions,
    CommandOptions_None
)

from . import commands
from . import error

class CommandManager(GObject.GObject):
    __name__ = "sgbackup-CommandManager"

    __gsignals__ = {
        'add': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,)),
        'add-alias': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,str)),
        'remove': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,)),
        'remove-alias': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,)),
        'execute': (GObject.SIGNAL_RUN_FIRST,int,(GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT)),
        'destroy': (GObject.SIGNAL_RUN_LAST,int,()),

    }
    def __init__(self):
        GObject.GObject.__init__(self)
        self.__commands={}
        self.__app = None

    def _real_initialize(self,app):
        if not self.is_initialized:
            self.__app = app
            for cmd_spec in commands.BUILTIN_COMMANDS:
                command = cmd_spec[0](self.application)

                if (cmd_spec[1]):
                    aliases = cmd_spec[1]
                else:
                    aliases = []

                self.add(command,aliases)

    @GObject.Property
    def application(self):
        return self.__app
    
    @GObject.Property
    def is_initialized(self):
        return (self.application is not None)

    def destroy(self):
        self.emit('destroy')

    def do_destroy(self):
        commands = []
        for cmd in self.__commands.values():
            if cmd not in commands:
                commands.append(cmd)

        for cmd in commands:
            cmd.destroy()

        self.__commands = {}
        self.__app = None

    def add(self,command:Command,aliases=None):
        self.emit('add',command)
        if aliases:
            for alias in aliases:
                self.add_alias(command,alias)

    def do_add(self,command:Command):
        self.__commands[command.id] = command

    def add_alias(self,command:Command,alias:str):
        self.emit('add-alias',command,alias)

    def do_add_alias(self,command:Command,alias:str):
        self.__commands[alias] = command

    def remove(self,command:Command):
        self.emit('remove',command)

    def do_remove(self,command:Command):
        keys=[]
        for key,value in self.__commands.items():
            if (command == value):
                keys.append(key)

        for key in keys:
            del self.__commands[key]

        command.destroy()

    def remove_alias(self,alias:str):
        self.emit('remove-alias',alias)

    def do_remove_alias(self,alias:str):
        if alias in self.__commands:
            command = self.__commands[alias]
            del self.__commands[alias]

            if not command in self.__commands.values():
                command.destroy()

    @GObject.Property
    def list(self):
        ret=[]
        for i in self.__commands.keys():
            ret.append(i)
        ret.sort()
        return ret
    
    def has_command(self,cmd):
        return (cmd in self.__commands)
    
    def get(self,cmd:str):
        if not cmd in self.__commands:
            raise error.CommandError('Command "{}" does not exist!'.format(cmd))
        return self.__commands[cmd]
    
    def parse(self,cmd:str,argv=[]):
        if not cmd in self.__commands:
            raise error.CommandError('Command "{}" does not exist!'.format(cmd))
        return self.__commands[cmd].parse(argv)

    def execute(self,cmd:str,options:CommandOptions):
        if not cmd in self.__commands:
            raise error.CommandError('Command "{}" does not exist!'.format(cmd))
        self.emit('execute',self.__commands[cmd])

    def do_execute(self,command,options):
        return command.execute(options)
    
    