# -*- coding:utf-8 -*-
# author: Christian Moser
# file: sgbackup/archiver/_archiver.py
# module: sgbackup.archiver._archiver
# license: GPL

from gi.repository import GObject
from ..game import Game

import os

class ArchiverBase(GObject.GObject):
    """
    Base class for archivers. Overload this class to implement your own archiver.

    :param app: Application instance. 

        **This parameter will be overgiven on creation.**
    :type app: :class:`sgbackup.application.Application`
    :param id: The archvier ID. The ID will be used for archiver lookups.

        **Set this parameter in the overloading class.**
    :type id: `str`
    :param extension: The extension to use for creating backup files.

        **Set this parameter in the overloading class.**
    :type extensions: `str`
    :param archive_extensions: A list of archive extensions to look for.
        
        **Set this parameter in the overloading class.**
    :type archive_extensions: `list(str)` or `None`
    :param multiprocessing: Does the archiver use multiprocessing/multithreading for archive creation. (Default: `False`)

        **Set this parameter in the overloading class.**
    :type multiprocessing: `bool`

    Signals
    _______
    * *backup*
    * *destroy*
    * *restore*

   """
    __name__ = "sgbackup.archiver._archiver.Archiver"
    __gsignals__ = {
        'backup': (GObject.SIGNAL_RUN_FIRST,None,(GObject.GObject,str)),
        'restore': (GObject.SIGNAL_RUN_FIRST,None,(Game,str)),
        'destroy': (GObject.SIGNAL_RUN_FIRST,None,()),
    }

    def __init__(self,app,id:str,extension:str,archive_extensions=None,multiprocessing=False):
        GObject.GObject.__init__(self)
        self.__id = id
        self.__ext = extension

        self.__app = app

        self.__extensions=[]
        if archive_extensions:
           for ext in archive_extensions:
               if not isinstance(ext,str):
                   raise TypeError("\"archive_extensions\" need to be a list of strings!")
               if ext.startswith('.'):
                    self.__extensions.append(ext[1:])
               else:
                    self.__extensions.append(ext)

        if not extension in self.__extensions:
            self.__extensions.insert(0,extension)

        self.__multiprocessing = multiprocessing

    @GObject.Property
    def application(self):
        """
        *(read only)*

        The application instance the archiver is registered to.

        :type: :class:`sgbackup.application.Application`
        """
        return self.__app
    
    @GObject.Property
    def is_initialized(self):
        """
        *(read only)*

        `True` if the class is initialized, `False` otherwise.

        :type: `bool`
        """
        return (self.__app is not None)
    
    @GObject.Property
    def id(self):
        """
        *(read only)*

        The id of the archiver. This value is set by the overloading class.

        :type: `str`
        """
        return self.__id
    
    @GObject.Property
    def extension(self):
        """
        *(read only)*

        The extension to use for creating archives. 
        
        :type: str
        """
        return self.__ext

    @GObject.Property
    def archive_extensions(self):
        """
        *(read only)*

        Alternative extensions to use for archive lookups.

        :type: `list(str)`
        """
        return self.__extensions
    
    @GObject.Property
    def extensions(self):
        """
        *(read only)*

        Same as `archive extensions`.

        :type: `list(str)`
        """
        return self.__extensions
    
    @GObject.Property
    def multiprocessing(self):
        """
        *(read only)*

        `True` if the archiver supports multiprocessing/multithreading, `False` otherwise.

        :type: `bool`
        """
        return self.__multiprocessing

    def backup(self,game,filename):
        """
        Create a game backup. This function emits the `backup` signal.

        :param game: The game to create the backup for.
        :type game: :class:`sgbackup.game.Game`
        :param filename: The filename of the backup to create.
        :type filename: `str`
        """
        if not os.path.exists(os.path.join(game.savegame_root,game.savegame_dir)):
            if self.application.config.verbose:
                print("!!! No savegames for \"{game}\"! SKIPPING!".format(game=game.game_name))
            return

        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
            
        self.emit('backup',game,filename)

    def do_backup(self,game,filename):
        """
        Create a savegame backup. If not overloaded this class raises a `NotImplementedError`!

        **This method should be overloaded by the archiver class.**
        """
        raise NotImplementedError("Backup for archiver \"{}\" is not implemented!")
    
    def restore(self,game,filename):
        """
        Restore a savegame backup.

        This method emits the `restore` signal.

        :param game: The game of the backup to restore.
        :type game: :class:`sgbackup.game.Game`
        :param filename: The filename of the savegame backup to restore.
        :type filename: `str`
        """
        if not os.path.exists(filename):
            print("!!! Backup-file \"{file}\" does not exist!".format(file=filename))
            return
        
        if not os.path.exists(game.savegame_root):
            print("!!! SaveGame root directory does not exist!")
            return
        
        self.emit('restore',game,filename)

    def do_restore(self,game,filename):
        """
        Restore a savegame backup. If not overloaded this class raises a `NotImplementedError`!

        **This method should be overloaded by the archiver class.**
        """
        raise NotImplementedError("Restore for archiver \"{}\" is not implemented!")
    
    def file_is_archive(self,filename):
        """
        Test if the file is a valid archive.

        :param filename: The name of the file to test.
        :type filename: `str`

        :returns: `True` if the file is a valid archive, `False` otherwise.
        """
        for i in self.archive_extensions:
            if i.startswith('.'):
                ext = i
            else:
                ext = '.' + i
        
            if filename.endswith(ext):
                return True
            
        return False

    def destroy(self):
        self.emit('destroy')

    def do_destroy(self):
        self.__app = None
