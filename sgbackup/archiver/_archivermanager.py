# -*- coding:utf-8 -*-
#author: Christian Moser
#file: sgbackup/archiver/_archivermanager.py
#module: sgbackup.archiver._archivermanager
#licenese: GPL

from gi.repository import GObject
from ..game import Game
from ._archiver import ArchiverBase
import fnmatch
import os
import sys

import datetime
#import sgbackup
from .zipfilearchiver import ZipfileArchiver
from .tarfilearchiver import (
    TarfileArchiver,
    TarfileBz2Archiver,
    TarfileGzArchiver,
    TarfileXzArchiver
)
from . import commandarchiver

class ArchiverManager(GObject.GObject):
    """
    This class holds the archivers used for backup and restore operations.

    Signals
    _______
    * *add-archiver*
    * *backup*
    * *backup-file*
    * *delete-backup*
    * *destroy*
    * *remove-archiver*
    * *restore*
    """
    __name__ = 'sgbackup.archiver._archivermanager.ArchiverManager'
    __gsignals__ = {
        'backup': (GObject.SIGNAL_RUN_FIRST,None,(ArchiverBase,Game,str)),
        'backup-file':(GObject.SIGNAL_RUN_FIRST,None,(Game,str)),
        'restore': (GObject.SIGNAL_RUN_FIRST,None,(ArchiverBase,Game,str)),
        'add-archiver': (GObject.SIGNAL_RUN_FIRST,None,(ArchiverBase,)),
        'remove-archiver': (GObject.SIGNAL_RUN_FIRST,None,(ArchiverBase,)),
        'destroy': (GObject.SIGNAL_RUN_LAST,None,()),
        'delete-backup': (GObject.SIGNAL_RUN_FIRST,None,(Game,str)),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.__app = None
        self.__archivers = {}

    def _real_initialize(self,app):
        self.__app = app

        app.config.connect('load-config',self.on_load_config)
        archivers = [
            ZipfileArchiver(app),
            TarfileArchiver(app),
            TarfileBz2Archiver(app),
            TarfileXzArchiver(app),
            TarfileGzArchiver(app),
        ]
        
        cmd_archivers = commandarchiver.get_archivers(self.application)
        if cmd_archivers:
            archivers += cmd_archivers

        for archiver in archivers:
            self.add_archiver(archiver)


    @GObject.Property
    def application(self):
        """
        *(read only)* 
        
        The application this class is registered with.

        :type: :class:`sgbackup.application.Application`
        """
        return self.__app
    
    @GObject.Property
    def is_initialized(self):
        """
        *(read only)*

        `True` if the class is properly initialized, `False` otherwise.

        :type: `bool`
        """
        return (self.__app is not None)

    @GObject.Property
    def standard_archiver(self):
        """
        The standard archiver for creating savegame backup archives.
        If the archiver given in the configurartion is not found 
        :class:`sgbackup.archiver.zipfilearchiver.ZipfileArchiver` is returned.

        You can set the standard archiver with an *ArchiverID* string or with 
        a :class:`sgbackup.archiver._archiver.ArchiverBase` instance.

        :type: :class:`sgbackup.archiver._archiver.ArchiverBase` instance.
        """
        id = self.application.config.get_string('sgbackup','archiver')
        if not self.__archivers:
            raise LookupError('Unable to lookup standard archiver! No archivers listed!')
        if id in self.__archivers:
            return self.__archivers[id]
        elif 'zipfile' in self.__archivers:
            return self.__archivers['zipfile']
        elif 'tarfile-xz' in self.__archivers:
            return self.__archivers['tarfile']
        elif 'tarfile-bzip2' in self.__archivers:
            return self.__archivers['tarfile:bzip2']
        elif 'tarfile' in self.__archivers:
            return self.__archivers['tarfile']
        else:
            for v in self.__archivers.values:
                return v
    @standard_archiver.setter
    def standard_archiver(self,archiver):
        if isinstance(archiver,ArchiverBase):
            if not archiver.id in self.__archivers:
                self.__archivers[archiver.id] = archiver
            self.application.config.set_string('sgbackup','archiver',archiver.id)
        elif isinstance(archiver,str):
            if not archiver in self.__archivers:
                raise ValueError("\"{archiver}\" is not a valid archiver id!".format(archiver=archiver))
            self.application.config.set_string("sgbackup","archiver",archiver)
        else:
            raise TypeError("Archiver is not valid archiver id or ArchiverBase instance!")
            

    def load_command_archivers(self):
        """
        Loads command archivers. This function is called on initialisation, 
        so there is no need to call it yourself.
        """
        archivers = commandarchiver.get_archivers(self.application)
        for i in archivers:
            self.add_archiver(i)

    def has_archiver(self,id:str):
        """
        Check if a archiver with a given id exists.
        :param id: Archiver ID
        :type id: `str`
        :returns: `True` if an archiver with the given ID exists, `False` otherwise.
        """
        return (id in self.__archivers)
    
    def get_archiver(self,id:str):
        """
        Get an archiver with a given `id`. If no archiver with `id` exists,
        a `LookupError` is raised.

        :param id: Archiver ID
        :type id: `str`
        :returns: The :class:`sgbackup.archiver._archiver.ArchiverBase` instance 
            of the given `id`.
        """
        if not id in self.__archivers:
            raise LookupError("archiver \"{}\" not found!".format(id))
        return self.__archiver[id]
    
    def add_archiver_class(self,archiver_class,*args,**kwargs):
        """
        Create a instance of an archiver class and add it to archivers.

        :param archiver_class: The Archiver class to create an instance of and to add.
        :type archiver_class: :class:`sgbackup.archiver._archiver.ArchiverBase` class.
        :param args: Arguments to add to archiver class creation.
        :type args: Arguments to add.
        :param kwargs: Keyword arguments to add to archiver class creation.
        :type kwargs: Keyword arguments.
        """
        archiver = archiver_class(self.application,*args,**kwargs)
        self.add_archiver(archiver)

    def add_archiver(self,archiver:ArchiverBase):
        """
        Add an :class:`sgbackup.archiver._archiver.ArchiverBase` instance to archivers.
        
        :param archiver: Archiver to add.
        :type archiver: :class:`sgbackup.archiver._archiver.ArchiverBase` instance.
        """
        self.emit('add-archiver',archiver)

    def do_add_archiver(self,archiver):
        """
        Add archiver signal callback.
        
        This callback does the real work of adding the archiver.
        """
        archiver._archivermanager_slot_backup = archiver.connect('backup',self.__on_archiver_backup)
        archiver._archivermanager_slot_restore = archiver.connect('restore',self.__on_archiver_restore)
        self.__archivers[archiver.id] = archiver

    def remove_archiver(self,archiver):
        """
        Remove an archiver from usable archivers.
        :param archiver: Archiver to remove.
        :type archiver: A :class:`sgbackup.archiver._archiver.ArchiverBase` instance or a `str`.
        """
        if isinstance(archiver,str):
            try:
                archiver = self.get_archiver(archiver)
            except LookupError:
                return
        elif not isinstance(archiver,ArchiverBase):
            raise TypeError("\"archiver\" needs to be am Archiver-ID or an \"ArchiverBase\"-instance!")
        
        self.emit("remove-archiver",archiver)

    def do_remove_archiver(self,archiver):
        """
        This 'remove' signal callback does the real work of removing an archiver.
        """
        if archiver.id in self.__archivers:
            if hasattr(archiver,'_archivermanager_slot_restore'):
                archiver.dicsonnect(archiver._archivermanager_slot_restore)
                del archiver._archivermanager_slot_restore
            if hasattr(archiver,'_archivermanager_slot_backup'):
                archiver.disconnect(archiver._archivermanager_slot_backup)
                del archiver._archivermanager_slot_backup
            del self.__archivers[archiver.id]

    @GObject.Property
    def archivers(self):
        """
        This property returns a list of all registered archivers.

        :type: `list`(:class:`sgbackup.archiver._archiver.ArchiverBase`)
        """
        return list(self.__archivers.values())
    
    def get_archivers(self):
        """
        Get a list of all registered archivers.

        :returns: A list of all regsitered archivers.
        """
        return list(self.__archivers.values())
    
    def file_is_archive(self,filename):
        """
        Checks is the given file is a valid archive.

        :param filename: Filename to check. This should be an absolute path.
        :type filename: `str`
        :returns: `True` if the given file is a valid archive, `False` otherwise.
        """
        for a in self.get_archivers():
            if a.file_is_archive(filename):
                return True
        return False
    
    def create_backup_name(self,game,archiver):
        """
        Generate a new filename for given game and given archiver. The filename
        contains the current date and current time and gets the filename extension of
        the given archiver. It also honors the finished flag.

        :param game: The game for which the backup should be created.
        :type game: :class:`sgbackup.game.Game`
        :param archiver: The archiver to use for the backup.
        :type archiver: :class:`sgbackup.archiver._archiver.ArchiverBase`
        :returns: A `str` containing the filename as an absolute path for a new backup archive.
        """
        if game.is_finished:
            filename = os.path.join(
                game.backup_dir,
                'finished',
                '.'.join((
                    game.savegame_name,
                    datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
                    archiver.extension
                ))
            )
        
        else:
            filename= os.path.join(
                game.backup_dir,
                'active',
                '.'.join((
                    game.savegame_name,
                    datetime.datetime.now().strftime("%Y%m%d-%H%M%S"),
                    archiver.extension
                ))
            )
        if self.application.config.platform_win32:
            return filename.replace('/','\\')
        return filename
    
    def get_archiver_for_file(self,filename):
        """
        Get an archiver for a given file.
        :param filename: The filename of the archive.
        :type filename: `str`
        :returns: An archiver for the file or `None` if no archiver for the file was found.
        """
        for i in self.standard_archiver.archive_extensions:
            if i.startswith('.'):
                ext = i
            else:
                ext = '.' + i

            if filename.endswith(ext):
                return self.standard_archiver

        for a in self.get_archivers():
            for i in a.archive_extensions:
                if i.startswith('.'):
                    ext = i
                else:
                    ext = '.' + i

                if filename.endswith(ext):
                    return a
        return None
        
    def backup(self,game,archiver=None):
        """
        Backup a game.

        :param game: The game to backup.
        :type game: :class:`sgbackup.game.Game`
        :param archiver: The archiver to use. If `archiver` is `None` the standard archiver is used.
        :type archiver: :class:`sgbackup.archiver._archiver.ArchiverBase` or `None`
        """
        if archiver is None:
            archiver = self.standard_archiver
        elif isinstance(archiver,str):
            archiver = self.get_archiver(archiver)
        elif not isinstance(archiver,ArchiverBase):
            raise TypeError("\"archiver\" has to be \"None\", an Archiver-ID or an \"ArchiverBase\" instance!")
        
        backup_name = self.create_backup_name(game,archiver)
        if not os.path.isdir(os.path.dirname(backup_name)):
            os.makedirs(os.path.dirname(backup_name))
        archiver.backup(game,backup_name)

    def __on_archiver_backup(self,archiver,game,filename):
        """
            Archivers `backup` signal callback. This method is called by registerd archivers.
            **DO NOT CALL THIS METHOD YOURSELF!**
        """
        self.emit('backup',archiver,game,filename)

    def do_backup(self,archiver,game,filename):
        """
        `backup` signal callback. This signal is emitted when an archiver
        backups a game.
        """
        max_backups = self.application.config.backup_versions
        if max_backups <= 0:
            return
        backups=[]

        for fname in sorted(game.active_backups,reverse=True):
            stat = os.stat(fname)
            inserted = False
            for i in range(len(backups)):
                if stat.st_ctime > backups[i][0]:
                    backups.insert(i,(stat.st_ctime,fname))
                    inserted = True
                    break
            if not inserted:
                backups.append((stat.st_ctime,fname))
        
        if len(backups) > max_backups:
            for i in range(max_backups,len(backups)):
                self.delete_backup(game,backups[i][1])

    def delete_backup(self,game:Game,filename:str):
        """
        Delete a savegame backup.

        :param game: The game the backup  belongs to.
        :type game: :class:`sgbackup.game.Game`
        :param filename: The backup file to delete. 
            This should be an absolute path.
        :type filename: `str`
        """
        if not os.path.isabs(filename):
            filename=os.path.join(game.backup_dir,filename)

        if not os.path.isfile(filename):
            return
        
        if self.application.config.is_win32:
            filename = filename.replace('/','\\')

        self.emit('delete-backup',game,filename)

    def do_delete_backup(self,game,filename):
        """
        This `delete-backup` signal callback does the real work of deleting
        the backup file.

        :param game: The game the backup belongs to.
        :type game: :class:`sgbackup.game.Game`
        :param filename: The backup file to delete. This is an absolute path.
        :type filename: `str`
        """
        if not os.path.isfile(filename):
            return
        
        if self.application.config.verbose:
            print("[delete backup] {}".format(os.path.basename(filename)))
        os.unlink(filename)

    def restore(self,game,backup):
        """
        Restore a savegame backup. If no archiver for the given backup is found,
        a `ValueError` is raised.

        :param game: The game the backup belong to.
        :type game: :class:`sgbackup.game.Game`
        :param backup: The filename of the backup to restore. 
            This should be an absolute path.
        :type backup: `str` 
        """
        archiver = self.get_archiver_for_file(backup)
        if not archiver:
            raise ValueError("File \"{}\" has no valid archiver!")
        
        archiver.restore(game,backup)
    
    def __on_archiver_restore(self,archiver,game,backup):
        """
        :classs:`gbackup.archiver._archiver.ArchiverBase` - signal *restore* callback.
        
        **Do not call this method yourself!**
        """
        self.emit('restore',archiver,game,backup)

    def do_restore(self,archiver,game,backup):
        """
        The `restore` signal callback.

        :param archiver: The archiver that is used for resotring the archive.
        :type archiver: :class:`sgbackup.archiver._archiver.ArchiverBase`
        :param game: The game the backup belongs to.
        :type game: :class:`sgbackup.game.Game`
        :param backup: The savegame backup to restore.
        :type backup: `str`
        """
        pass
    
    def destroy(self):
        self.emit('destroy')

    def do_destroy(self):
        """
        **destroy** signal callback. This callback destroys the class.

        **Do not call this method yourself!**
        """
        try:
            for archiver in self.__archivers.values():
                if hasattr(archiver,'_archivermanager_slot_backup'):
                    archiver.disconnect(archiver._archivermanager_slot_backup)
                    archiver._archivermanager_slot_backup
                if hasattr(archiver,'_archivermanager_slot_restore'):
                    archiver.disconnect(archiver._archivermanager_slot_restore)
                    del archiver._archivermanager_slot_restore

                archiver.destroy()
        except:
            pass
        self.__archivers={}            

    def get_game_backups(self,game):
        """
        Get savegame all backups for given game.

        :param game: The game to get the backups for.
        :type game: :class:`sgbackup.game.Game`
        :returns: (`list(str)`) - A list of savegame backups for a given game.
            The backup-string is an absolute path of the backup archive.
            If not backup is found, an empty list is returned.
        """
        ret = []
        if not os.path.isdir(game.backup_dir):
            return ret
        
        for i in os.listdir(game.backup_dir,'active'):
            fname = os.path.join(game.backup_dir,'active',i)
            if (os.path.isfile(fname) 
                and self.file_is_archive(fname)
                and fnmatch.fnmatch(i,'{}.????????-??????.*'.format(game.savegame_name))):
                if self.application.config.platform_win32:
                    fname = fname.replace('/','\\')
                ret.append(fname)
        for i in os.listdir(game.backup_dir,'finished'):
            fname = os.path.join(game.backup_dir,'finished',i)
            if (os.path.isfile(fname) 
                and self.file_is_archive(fname)
                and fnmatch.fnmatch(i,"{}.????????-??????.*".format(game.savegame_name))):
                if self.application.config.platform_win32:
                    fname = fname.replace("/","\\")
                ret.append(fname)
        return ret
    
    def get_active_game_backups(self,game):
        """
        Get active game backups for a given game.

        :param game: The game to get active backups for.
        :type game: :class:`sgbackup.game.Game`
        :returns: (`list(str)`) - A list of active savegame backups.
            The backup-string is an absolute path of the backup archive.
            If no active backup is found an empty list is returned.
        """
        ret = []

        backup_dir = os.path.join(game.backup_dir,'active')
        if not os.path.isdir(backup_dir):
            return ret
        
        for i in os.listdir(backup_dir):
            fname = os.path.join(backup_dir,i)
            if (os.path.isfile(fname) 
                and self.file_is_archive(fname) 
                and fnmatch.fnmatch(i,"{}.????????-??????.*".format(game.savegame_name))):
                if self.application.config.platform_win32:
                    fname = fname.replace('/','\\')
                ret.append(fname)
        return ret
    
    def get_finished_game_backups(self,game):
        """
        Get finished savegame backups for a given game.

        :param game: The game to get active backups for.
        :type game: :class:`sgbackup.game.Game`
        :returns: (`list(str)`) - A list of active savegame backups.
            The backup-string is an absolute path of the backup archive.
            If no finished backup is found an empty list is returned.
        """
        ret = []

        backup_dir = os.path.join(game.backup_dir,'finished')
        if not os.path.isdir(backup_dir):
            return ret
        
        for i in os.listdir(backup_dir):
            fname = os.path.join(backup_dir,i)
            if (os.path.isfile(fname)
                and self.file_is_archive(fname)
                and fnmatch.fnmatch(i,"{}.finished.????????-??????.*".format(game.savegame_name))):
                if self.application.config.platform_win32:
                    fname = fname.replace('/','\\')
                ret.append(fname)
        return ret
    
    def get_latest_finished_game_backup(self,game):
        """
        Get the latest finished savegame backup for a given game.

        :param game: The game to get the finished backup for.
        :type game: :class:`sgbackup.game.Game`
        :returns: (`str`) - The latest finished backup as an absolute path to the archive file.
            If no finished backup is found `None` is returned.
        """
        for i in sorted(self.get_finished_game_backups(game),reverse=True):
            return i
        return None
    
    def get_latest_active_game_backup(self,game):
        """
        Get the latest finished savegame backup for a given game.

        :param game: The game to get active backup for.
        :type game: :class:`sgbackup.game.Game`
        :returns: (`str`) - The latest active backup as an absolute path to the archive file.
            If no active backup is found `None` is returned.
        """
        for i in sorted(self.get_active_game_backups(game),reverse=True):
            return i
        return None
        
    def get_latest_game_backup(self,game):
        """
        Get latest savegame backup.

        :param game: The game for which to lookup the latest backup.
        :type game: :class:`sgbackup.game.Game`
        :returns: The latest savegame backup made for the given game 
            or `None` if no backup was found.
        """
        latest_backup=None
        latest_backup_datetime=None
        def get_datetime_from_backup(backup):
            fn = os.path.basename(backup)
            try:
                dt_string = fn[len(game.savegame_name)+1:len(game.savegame_name)+16]
                return datetime.datetime.strptime(dt_string,"%Y%m%d-%h%m%s")
            except:
                pass
            return None
        
        for i in self.get_game_backups(game):
            backup_datetime = get_datetime_from_backup(i)
            if backup_datetime is None:
                continue

            if latest_backup_datetime is None or (backup_datetime > latest_backup_datetime):
                latest_backup = i
                latest_backup_datetime = backup_datetime

        return latest_backup
    
    def on_load_config(self,config,cfgparser):
        pass

    def backup_file(self,game,file):
        """
        Backup an extra file, which is not a savegame backup archive.

        This method emits the *backup-file* signal.

        :param game: The game the file belongs to.
        :type game: :class:`sgbackup.game.Game`
        :param file: The filename to backup. The filename should be an
            absolute path.
        :type file: `str`
        """
        self.emit('backup-file',game,file)

    def on_backup_file(self,game,file):
        """
        *backup-file* signal callback.

        **Do not call this method yourself!**
        """
        pass
