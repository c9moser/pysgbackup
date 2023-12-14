# -*- coding: utf-8 -*-

# Author: Christian Moser
# License: GPL
# File: sgbackup/commandmanager.py
# Module: sgbackup.commandmanager

from gi.repository import GObject
from . import command
from .command import (
    Command,
    CommandOptions,
    CommandOptions_None
)

from . import commands
from . import error

class CommandManager(GObject.GObject):
    """
    This class manages the commands used in *pysgbackup*.

    It holds the commands and has a lookup dict for the cmmands and its aliases.
    It also provides methods to add and remove commands dynamically, which can be used 
    for example by GUI-programs using *pysgbackp*.

    SIGNALS
    ^^^^^^^
    * *add*
    * *add-alias*
    * *destroy*
    * *execute*
    * *parse*
    * *remove*
    * *remove-alias*
    """
    __name__ = "sgbackup-CommandManager"

    __gsignals__ = {
        'add': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,)),
        'add-alias': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,str)),
        'remove': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,)),
        'remove-alias': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,)),
        'parse': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,str,GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT)),
        'execute': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT)),
        'destroy': (GObject.SIGNAL_RUN_LAST,None,()),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.__commands={}
        self.__app = None

    def _real_initialize(self,app):
        """
        Called by the application that is instantiating this class.
        """
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
        """
        The application the instance of this class belongs to.
        
        :type: :class:`sgbackup.application.Application`
        """
        return self.__app
    
    @GObject.Property
    def is_initialized(self):
        """
        `True` if this class is properly initialized and not destroyed, `False` otherwise.
        
        :type: `bool`
        """
        return (self.application is not None)

    def destroy(self):
        """
        Destroy the instance of this class.
        This method is called by :class:`sgbackup.application.Application`.

        There should be no reason to call this method yourself!
        """
        self.emit('destroy')

    def do_destroy(self):
        """
        *destroy* signal handle.
        """
        commands = []
        for cmd in self.__commands.values():
            if cmd not in commands:
                commands.append(cmd)

        for cmd in commands:
            cmd.destroy()

        self.__commands = {}
        self.__app = None

    def add(self,command:Command,aliases=None):
        """
        Add a new command.

        :param command: The command to be added.
        :type command: :class:`sgbackup.command.Command`
        :param aliases: Initial aliases for the command. This should be `None` 
            if no aliases are added or a `list` of alias strings.
        :type aliases: `None` or `list(str)`
        """
        self.emit('add',command)
        if aliases:
            for alias in aliases:
                self.add_alias(command,alias)

    def do_add(self,command:Command):
        """
        The *add* signal handle. This method really adds the command to the lookup table.
        
        :param command: The command to be added.
        :type command: :class:`sgbackup.command.Command`
        """
        command._commandmanager_slot_parse = command.connect('parse',self.__on_command_parse)
        command._commandmanager_slot_execute = command.connect('execute',self.__on_command_execute)
        command._commandmanager_slot_destroy = command.connect('destroy',self.__on_command_destroy)

        self.__commands[command.id] = command

    def add_alias(self,command:Command,alias:str):
        """
        Add an alias for a command.

        :param command: The command for which an lias should be added.
        :type command: :class:`sgbackup.command.Command`
        :param alias: The alias to be added.
        :type alias: `str`
        """
        self.emit('add-alias',command,alias)

    def do_add_alias(self,command:Command,alias:str):
        """
        The *add-alias* signal handle. This method really adds the alias
        to the lookup table.

        :param command: The command for which the alias is to be added.
        :type command: :class:`sgbackup.command.Command`
        :param alias: The alias to be added.
        :type alias: `str`
        """
        self.__commands[alias] = command

    def remove(self,command):
        """
        Remove a command and all of its aliases.

        :param command: A command string or a :class:`sgbackup.command.Command` instance.
            If a string is used, it can also be an alias.
        :type command: `str` or :class:`sgbackup.command.Command`
        """

        if isinstance(command,str):
            if self.has_command(command):
                command = self.__commands[command]
            else:
                return
        elif not isinstance(command,Command):
            raise TypeError("\"command\" is not a command string or a \"sgbackup.Command\" instance!")

        self.emit('remove',command)

    def do_remove(self,command:Command):
        """
        The *remove* signal handle. This method does the real work of removing a command.
        
        :param command: The command to be removed.
        :type command: :class:`sgbackup.command.Command`
        """
        keys=[]
        for key,value in self.__commands.items():
            if (command == value):
                keys.append(key)

        for key in keys:
            del self.__commands[key]

        command.destroy()

    def remove_alias(self,alias:str):
        """
        Remove an alias of a command. If there are no command-ids left for a command,
        the command is destroyed.

        :param alias: The alias to be removed.
        :type alias: `str`
        """
        self.emit('remove-alias',alias)

    def do_remove_alias(self,alias:str):
        """
        The *remove-alias* signal handle. This method does the real work of removing
        the alias.

        :param alias: The alias to be removed.
        :type alias: `str`
        """
        if alias in self.__commands:
            command = self.__commands[alias]
            del self.__commands[alias]

            if not command in self.__commands.values():
                command.destroy()

    def __on_command_destroy(self,command):
        if hasattr(command,"_commandmanager_slot_parse"):
            command.disconnect(command._commandmanager_slot_parse)
            del command._commandmanager_slot_parse
        if hasattr(command,"_commandmanager_slot_execute"):
            command.disconnect(command._commandmanager_slot_execute)
            del command._commandmanager_slot_execute
        if hasattr(command,"_commandmanager_slot_destroy"):
            command.disconnect(command._commandmanager_slot_destroy)
            del command._commandmanager_slot_destroy

    @GObject.Property
    def list(self):
        """
        A list of all available commands and aliases.

        :type: `list(str)`
        """
        ret=[]
        for i in self.__commands.keys():
            ret.append(i)
        ret.sort()
        return ret
    
    def has_command(self,cmd):
        """
        Check if a command or alias is available.

        :returns: `True` if the command or alias is available, `False` otherwise.
        """
        return (cmd in self.__commands)
    
    def get(self,cmd:str):
        """
        Get a command. If the command does not exists a 
        :class:`sgbackup.error.CommandError` is raised.

        :param cmd: A command or alias.
        :type cmd: `str`
        :returns: The requested :class:`sgbackup.command.Command` instance.
        """
        if not cmd in self.__commands:
            raise error.CommandError('Command "{}" does not exist!'.format(cmd))
        return self.__commands[cmd]
    
    def parse(self,cmd:str,argv=[]):
        """
        Parse command line args of a given command.

        If the command does not exist, a :class:`sgbackup.error.CommandError` 
        is raised.

        If this method succeeds, you should call :func:`execute` afterwards.

        :param cmd: The command for which the arguments should be parsed.
        :type cmd: `str` or :class:`sgbackup.command.Command`
        :param argv: The argument list to be parsed. The argument list
            should start with arguments and not with the command.
        :type argv: `list(str)`
        :returns: The :class:`sgbackup.command.CommandOptions` for
            the command to be executed afterwards.
        """
        if isinstance(cmd,str):
            if not cmd in self.__commands:
                raise error.CommandError('Command "{}" does not exist!'.format(cmd))
            command = self.__commands[cmd]
        elif isinstance(cmd,Command):
            command = cmd
            cmd = command.id
        else: 
            raise TypeError("\"cmd\" is not a string or a \"sgbackup.Command\" instance!")
        return command.parse(cmd,argv)

    def __on_command_parse(self,command,cmd,argv,options):
        self.emit("parse",command,cmd,argv,options)

    def do_parse(self,command,cmd,argv,options):
        """
        The *parse* signal handle.

        :param command: The command instance used for parsing.
        :type command: :class:`sgbackup.command.Command`
        :param cmd: The command string used to lookup the command.
        :type cmd: `str`
        :param argv: The argument vector to be parsed.
        :type argv: `list(str)`
        :param options: The options returned by the parser.
        :type options: :class:`sgbackup.command.CommandOptions`
        """
        pass

    def execute(self,cmd,options:CommandOptions):
        """
        Execute a command.

        :param cmd: The command to be executed.
        :type cmd: `str` or :class:`sgbackup.command.Command`
        :param options: The options used for the command. 
            This should be the options returned by :func:`parse`.
        :type options: :class:`sgbackup.command.CommandOptions`
        """
        if isinstance(cmd,Command):
            ret = command.execute(options)
        elif isinstance(cmd,str):
            if not cmd in self.__commands:
                raise error.CommandError('Command "{}" does not exist!'.format(cmd))
            ret = self.__commands[cmd].execute(options)
        else:
            raise TypeError("\"cmd\" is not a sgbackup.Command instance or a command id!")

        return ret

    def __on_command_execute(self,command,options):
        self.emit('execute',command,options)

    def do_execute(self,command,options):
        """
        *execute* signal handle.

        :param command: The command instance to be executed.
        :type command: :class:`sgbackup.command.Command`
        :param options: The options used for execution.
        :type options: :class:`sgbackup.command.CommandOptions`
        """
        pass
    