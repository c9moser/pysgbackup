# -*- coding:utf-8 -*-
# author: Christian Moser
# file: sgbackup/command.py
# module: sgbackup.command
# license: GPL

from . import error
from gi.repository import GObject
from .help import get_default_help

class CommandOptions(object):
    def __init__(self,app,id:str,cmd:str):
        self.__id = id
        self.__cmd = cmd
        self.__app = app

    @property
    def application(self):
        return self.__app
    
    @property
    def id(self):
        return self.__id
    
    @property
    def command(self):
        return self.__cmd

class CommandOptions_None(CommandOptions):
    OPTION_ID = "command-options-none"

    def __init__(self,app,command:str):
        CommandOptions.__init__(self,app,self.OPTION_ID,command)

class Command(GObject.GObject):
    __name__ = "sgbackup-command-Command"
    __gsignals__ = {
        'execute': (GObject.SIGNAL_RUN_FIRST,int,(GObject.TYPE_PYOBJECT,)),
        'destroy': (GObject.SIGNAL_RUN_LAST,None,()),
    }

    def __init__(self,app,id,description=""):
        GObject.GObject.__init__(self)
        self.__id = id
        self.__app = app
        self.__description = description

    @GObject.Property
    def id(self):
        return self.__id
    
    @GObject.Property
    def application(self):
        return self.__app

    @GObject.Property
    def is_initialized(self):
        return (self.application is not None)
    
    @GObject.Property
    def description(self):
        return self.__description
    
    def destroy(self):
        self.emit('destroy')

    def do_destroy(self):
        self.__app = None

    def get_synopsis(self,command=None):
        if command is None:
            command = self.id
        return "sgbackup {command}".format(command=command)
    
    def get_help_synopsis(self,command=None):
        ret = ""
        for line in self.get_synopsis(command).split("\n"):
            ret += "    {}\n".format(line)
        return ret


    def get_help(self,command=None):
        if command is None:
            command = self.id

        return get_default_help(command,self.get_help_synopsis(command))
    
    def parse(self,cmd,argv):
        return self.do_parse(cmd,argv)

    def do_parse(self,cmd,argv):
        if len(argv) > 0:
            raise error.InvalidOptionError()
        return CommandOptions_None(self.app,cmd)
    
    def execute(self,options:CommandOptions):
        try:
            return self.emit('execute',options)
        except Exception as error:
            print("Command \"{command}\" failed! ({error})".format(command=options.command,error=error))
            return 1

    def do_execute(self,options):
        msg = "\"execute\" for command \"{}\" is not implementd!".format(self.id)
        raise NotImplementedError(msg)
