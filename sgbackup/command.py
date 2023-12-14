# -*- coding:utf-8 -*-
# author: Christian Moser
# file: sgbackup/command.py
# module: sgbackup.command
# license: GPL

from . import error
from gi.repository import GObject
from .help import get_default_help
import sys

class CommandOptions(object):
    """
    Options for commands.

    This class should be olverloaded and passed to the command
    as options.

    :param app: The application the command belongs to.
    :type app: :class:`sgbackup.application.Application`
    :param id: The id of the command. The id should be used to check
        if the option belongs to the command.
    :type id: `str`
    :param command: The command string used to call the corresponding command.
        This can also be an alias of the command.
    :type command: `str`
    """
    def __init__(self,app,id:str,command:str):
        self.__id = id
        self.__cmd = command
        self.__app = app

    @property
    def application(self):
        """
        *read-only*

        The application the command belongs to.

        :type: `str`
        """
        return self.__app
    
    @property
    def id(self):
        """
        *read only*

        The id of the command.

        :type: `str`
        """
        return self.__id
    
    @property
    def command(self):
        """
        *read only*

        The command string used to call the command. 
        This can also be an alias of the actual command string.

        :type: `str`
        """
        return self.__cmd

class CommandOptions_None(CommandOptions):
    """
    An empty options class. This class can be used 
    for commands that don't have any options.

    The *id* defaults to *command-options-none*.

    :param app: The application the command belongs to.
    :type app: :class:`sgbackup.application.Application`
    :param command: The command string used to call the command.
        This can also be an alias of the actual command string.
    :type command: `str`
    """

    OPTION_ID = "command-options-none"

    def __init__(self,app,command:str):
        CommandOptions.__init__(self,app,self.OPTION_ID,command)

class Command(GObject.GObject):
    """
    This class implements an actual command.

    :param app: The application the command should be registerd to.
    :type app: :class:`sgbackup.application.Application`
    :param id: The command id. The id is used as initial command string.
    :type id: `str`
    :param description: A short description about the command.
    :type description: `str` or `None`
    
    SIGNALS
    ^^^^^^^
    * destroy
    * execute
    * parse
    """

    __name__ = "sgbackup-Command"
    __gsignals__ = {
        'execute': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,)),
        'destroy': (GObject.SIGNAL_RUN_LAST,None,()),
        'parse': (GObject.SIGNAL_RUN_FIRST,None,(str,GObject.TYPE_PYOBJECT,GObject.TYPE_PYOBJECT)),
    }

    def __init__(self,app,id,description=None):
        GObject.GObject.__init__(self)
        self.__id = id
        self.__app = app
        if description is None:
            self.__description = ""
        elif isinstance(description,str):
            self.__description = description
        else:
            raise TypeError("description")

    @GObject.Property
    def id(self):
        """
        *read only*

        The id of the command. This string is used as initial command string.

        :type: `str`
        """
        return self.__id
    
    @GObject.Property
    def application(self):
        """
        *read only* 
        
        The application the command is registered to.

        :type: `str`
        """
        return self.__app

    @GObject.Property
    def is_initialized(self):
        """
        *read only* 

        `True` if the command is properly initialized and not destroyed, 
        `False` otherwise.

        :type: `bool`
        """
        return (self.application is not None)
    
    @GObject.Property
    def description(self):
        """
        *read only*

        The description of the command. If no description is set this 
        property returns an empty string.

        :type: `str`
        """
        return self.__description
    
    def destroy(self):
        """
        Destroy the command. This method is called on command removal.

        **You should not call this method yourself!**
        """
        self.emit('destroy')

    def do_destroy(self):
        """
        *destroy* signal handle.

        **Do not call this method yourself!**
        """
        self.__app = None

    def get_synopsis(self,command=None):
        """
        Get the synopsis of the command.
        
        Overload this method and return a synopsis/usage string
        of the command you are implementing.

        :param command: The command string used to call the command.
        :type command: `str`
        :returns: The synopsis of the overloaded command as a string.
        """
        if command is None:
            command = self.id
        return "sgbackup {command}".format(command=command)
    
    def get_help_synopsis(self,command=None):
        """
        Get the synopsis string formated for the command help.

        :param command: The command string used to call this command.
        :type command: `str`
        :returns: The formatted synopsis string.
        """
        ret = ""
        for line in self.get_synopsis(command).split("\n"):
            ret += "    {}\n".format(line)
        return ret


    def get_help(self,command=None):
        """
        Get the help for the command. If this method is not
        overloaded it returns a default help message just containing
        the synopsis for the command.

        Overload this method and return a help string for the command
        you are implementing.

        :param command: The command string used to call this command.
        :type command: `str`
        :returns: The help for the command.
        """
        if command is None:
            command = self.id

        return get_default_help(command,self.get_help_synopsis(command))
    
    def parse(self,cmd,argv):
        """
        Parse the argument vector for a command.

        :param cmd: The command string used.
        :type cmd: `str`
        :param argv: The argument vector of the command to parse.
            The argument vector should start with the arguments and **not**
            with the command to be parsed.

        :returns: A :class:`sgbackup.command.CommandOptions` instance used
            as options for the command to execute.
        """
        options =  self.parse_vfunc(cmd,argv)
        try:
            self.emit('parse',cmd,argv,options)
        except Exception as err:
            print(err,file=sys.stderr)
        return options

    def parse_vfunc(self,cmd,argv):
        """
        This method is meant to be overloaded by the implemented command. 
        It is called by parse before the parse signal is emitted.

        This method should do the real parsing of command line arguments presented in
        the *argv* vector and return an :class:`sgbackup.command.CommandOptions`
        instance.

        :param cmd: The command-string used to call the command. 
            This can also be an alias for the actual command.
        :type cmd: `str`
        :param argv: A list of command-line arguments. This list starts with the
            first argument and not with the command called!
        :type argv: `list(str)`
        :returns: :class:`sgbackup.command.CommandOptions` instance representing
            the options and arguments for the command needed for execution.
        """
        if len(argv) > 0:
            raise error.InvalidOptionError("Command {command} does not take any arguments!".format(command=cmd))
        return CommandOptions_None(self.app,cmd)
    
    def do_parse(self,cmd,argv,options):
        pass
    
    def execute(self,options:CommandOptions):
        """
        Execute the command. This method calls the :func:`execute-vfunc`
        method.

        When the execution of the command succeeded, the *execute* signal is emitted.

        :param options: The options needed to execute the command.
        :type options: :class:`sgbackup.command.CommandOptions`
        :returns: `0` on success or an integer value if the execution failed.
        """
        try:
            ret = self.execute_vfunc(options)
            if ret is None:
                ret = 0
        except Exception as error:
            print("Command \"{command}\" failed! ({error})".format(command=options.command,error=error),file=sys.stderr)
            return 1
        
        if ret == 0:
            try:
                self.emit('execute',options)
            except Exception as error:
                print(error,file=sys.stderr)

        return ret

    def execute_vfunc(self,options:CommandOptions):
        """
        Do the real work when executing the command.

        This method is meant to be overloaded by the implemented
        command. If this method is not overloaded, a `NotIpmlementedError` 
        is raised and the command cannot be executed.

        On success `0` should be returned. If the execution of the
        command fails, an integer value should be returned. Uncought
        :class:`Exception` instances are handled by the calling 
        :func:`execute` and `1` is returned by the calling function.

        :param options: The options/settings for the command to execute.
        :type options: :class:`sgbackup.command.CommandOptions`
        :returns: `0` on success, an integer otherwise.
        """
        msg = "\"execute\" for command \"{}\" is not implementd!".format(self.id)
        raise NotImplementedError(msg)
    
    def do_execute(self,options):
        pass

