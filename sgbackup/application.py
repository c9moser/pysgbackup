# -*- coding: utf-8 -*-
# author: Christian Moser
# file: sgbackup/application.py
# module sgbackup.application
# license: GPL

from gi.repository import GObject
from .config import Config
from .archiver import ArchiverManager
from .gamemanager import GameManager
from .commandmanager import CommandManager
from .steam import Steam

from .plugin import PluginManager

from . import error
import sys

class Application(GObject.GObject):
    """
    This is the main Application class. It holds all of the required application interfaces.
    You can overload this class if you implement your own application. 
    
    To simply run from command line arguments call :func:sgbackup.application.Application.run().

    If you plan to create your own interface, like a GUI, you need to initialize this class by 
    calling :func:`Application.initialize` after creation.

    This class is exported to the `sgbackup` namespace sou you can access the class as 
    `sgbackup.Application`.

    Signals
    _______
    * `destroy` - Called when the app is destroyed.

    Members
    _______
    """
    __name__ = 'sgbackup.applicaction.Application'
    __gsignals__ = {
        'destroy': (GObject.SIGNAL_RUN_LAST,None,())
    }
    
    def __init__(self):
        GObject.GObject.__init__(self)
        self.__is_destroyed = False
        self.__config = Config()
        self.__archivers = ArchiverManager()
        self.__games = GameManager()
        self.__steam = Steam()
        self.__commands = CommandManager()
        self.__plugins = PluginManager()
        self.__is_initialized = False


    def __del__(self):
        if not self.__is_destroyed:
            self.destroy()

    def __real_initialize(self):
        self.config._real_initialize(self)
        self.archivers._real_initialize(self)
        self.games._real_initialize(self)
        self.steam._real_initialize(self)
        self.commands._real_initialize(self)
        self.plugins._real_initialize(self)
        self.__is_initialized = True

    @GObject.Property(bool)
    def is_initialized(self):
        """
        `True` if this class is fully initialized, `False` otherwise.
        """
        return (self.__is_initialized and not self.__is_destroyed)

    GObject.Property(bool)
    def is_destroyed(self):
        """
        `True` if class is already destroyed, `False` otherwise.
        """
        return self.__is_destroyed
    
    @GObject.Property
    def config(self):
        """
        The configuration for this app.
        (:class:`sgbackup.config.config.Config`)
        """
        return self.__config
    
    @GObject.Property
    def archivers(self):
        """
        The ArchiverManager for this app.
        (:class:`sgbackup.archiver._archivermanager.ArchiverManager`)
        """
        return self.__archivers
    
    @GObject.Property
    def games(self):
        """
        The GameManager.
        (:class:`sgbackup.gamemanager.GameManager`)
        """
        return self.__games

    @GObject.Property
    def steam(self):
        """
        Steam support for this application.
        (:class:`sgbackup.steam.Steam`)
        """
        return self.__steam
    
    @GObject.Property
    def commands(self):
        """
        The CommandManager.
        (:class:`sgbackup.commandmanager.CommandManager`)
        """
        return self.__commands
    
    @GObject.Property
    def plugins(self):
        """
        The PluginManager.
        (:class:`sgbackup.plugin.PluginManager`)
        """
        return self.__plugins

    def parse_argv(self,argv):
        """
        Parses an argument vector. This method returns a
        list of `(command,options)` tuples.
        
        :returns: A `list` of (command,options) tuples.
        """
        arg_list=[]

        is_option = True
        is_command = False

        for i in range(len(argv)):
            opt = argv[i]
            if is_option:
                if (opt.startswith('-')):
                    if opt in ('-v','--verbose'):
                        self.config.verbose = True
                    elif opt in ('-V','--no-verbose'):
                        self.config.verbose = False
                    elif opt == '--version':
                        print ("pysgbackup - {}", self.config.version)
                        exit(0)
                    else:
                        print('Unknown option {}',opt)
                else:
                    is_option = False
                    arg_list.append((argv[i],[]))
            elif is_command:
                arg_list.append((argv[i],[]))
                is_command = False
            elif argv[i] == '--':
                is_command = True
            else:
                arg_list[-1][1].append(argv[i])

        command_list=[]
        for cmd,argvec in arg_list:
            command = self.commands.get(cmd)
            options = command.parse(cmd,argvec)
            command_list.append((command,options))
                    
        return command_list


    def initialize(self):
        """
        Initializes the app and all submodules.
        If the app is already initialized, this method does nothing.
        """
        if not self.__is_initialized:
            self.__real_initialize()

    def run(self,argv):
        """
        Run the application with commandline arguments.
        
        Returns `0` on secuess. An integer otherwise.
        """
        self.initialize()

        try:
            command_list = self.parse_argv(argv)
        except Exception as err:
            print(err,file=sys.stderr)
            if isinstance(err,error.CommandError):
                print("Use \"sgbackup commands\" to list available commands.")
            return 2

        if not command_list:
            c = self.commands.get('synopsis')
            o = c.parse('synopsis',[])
            c.execute(o)
        else:
            for c,o in command_list:
                try:
                    c.execute(o)
                except Exception as err:
                    print(err,file=sys.stderr)    
                    return 1
            
        return 0

    
    def destroy(self):
        """
        Destroys the class and all submodules.
        This method is automatically called, when the application
        is deleted. There should be no reason to call this method
        yourself.
        """
        self.emit('destroy')

    def do_destroy(self):
        """
        Destroy signal callback.
        This callback does the real work.

        **Do not call this method yourself.**
        """
        if not self.__is_destroyed:
            try:
                self.plugins.destroy()
            except:
                pass

            try:
                self.commands.destroy()
            except:
                pass

            try:
                self.games.destroy()
            except:
                pass

            try:
                self.archivers.destroy()
            except:
                pass

            try:
                self.config.destroy()
            except:
                pass

        self.__is_destroyed = True
