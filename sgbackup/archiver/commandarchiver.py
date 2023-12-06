# -*- coding: utf-8 -*-
# author: Christian Moser
# file sgbackup/archiver/commandarchiver.py
# module sgbackup.archiver.commandarchiver

from gi.repository import GObject,GLib
from ._archiver import ArchiverBase
import os
import sys
import shlex
from string import Template
import subprocess

class CommandArchiver(ArchiverBase):
    def __init__(self,app,name,default_extension,extensions,exe,backup_args,restore_args,
                 verbose="",change_directory=True,variables=None,cygpath=None,multiprocessing=False):
        ArchiverBase.__init__(self,app,name,default_extension,extensions,multiprocessing)

        self.__exe = exe
        self.__backup_args = backup_args
        self.__restore_args = restore_args
        self.__change_directory = change_directory
        self.__variables = variables
        self.__verbose = verbose
        self.__cygpath = cygpath

    @staticmethod
    def new_from_file(app,filename:str):
        if not os.path.isfile(filename):
            return None
        section='archiver'
        kf = GLib.KeyFile()
        kf.load_from_file(filename,0)

        try:
            name = kf.get_string(section,"name")
            command = kf.get_string(section,"executable")
            backup_args = kf.get_string(section,"backupArgs")
            restore_args = kf.get_string(section,"restoreArgs")
            ext = kf.get_string(section,"extension")
            verbose = ""
            try:
                verbose = kf.get_string(section,'verbose')
            except:
                pass

            while ext.startswith('.'):
                ext = ext[1:]

            if not ext:
                return None

            extensions = []
            try:
                test_extensions = kf.get_string_list(section,"altExtensions")
                for i in range(len(test_extensions)):
                    while test_extensions[i].startswith('.'):
                        test_extensions[i] = test_extensions[i][1:]
                        if test_extensions[i]:
                            extensions.append(test_extensions[i])
            except:
                pass
 
            if not ext in extensions:
                extensions.insert(0,ext)

            try:
                change_directory = kf.get_boolean(section,"changeDirectory")
            except:
                change_directory = True

            cygpath = None
            try:
                cygpath = kf.get_string(section,'cygpath')
            except:
                pass

            if not cygpath:
                cygpath = None

            try:
                multiprocessing = kf.get_boolean(section,'multiprocessing')
            except:
                multiprocessing = False

            variables = {}
            if kf.has_group('variables'):
                keys,length = kf.get_keys('variables')
                if keys:
                    for vname in keys:
                        try:
                            variables[vname] = kf.get_string('variables',vname)
                        except:
                            pass

            return CommandArchiver(
                app,
                name,
                ext,
                extensions,
                command,
                backup_args,
                restore_args,
                verbose,
                change_directory,
                variables,
                cygpath,
                multiprocessing)
        except:
            return None

    @GObject.Property
    def executable(self):
        return self.__exe
    
    @GObject.Property
    def is_valid(self):
        if self.cygpath:
            return (os.path.isfile(self.cygpath) and os.path.isfile(self.executable))
        
        return os.path.isfile(self.executable)
        
    @GObject.Property
    def can_backup(self):
        return bool(self.__backup_args)
    
    @GObject.Property
    def can_restore(self):
        return bool(self.__restore_args)
    
    @GObject.Property
    def change_directory(self):
        return self.__change_directory
        
    @GObject.Property
    def verbose(self):
        if self.application.config.verbose:
            return self.__verbose
        return ""
    
    @GObject.Property
    def cygpath(self):
        return self.__cygpath
    
    def get_variables(self,game,filename):
        def sanitize_path(path):
            if self.cygpath:
                proc = subprocess.run([self.cygpath,'-u',path],capture_output=True)
                if proc.returncode == 0:
                    return proc.stdout.decode('utf-8').rstrip()
                else:
                    print(proc.stderr.decode('utf-8'),end="",file=sys.stderr)
                    raise RuntimeError()
            elif sys.platform == 'win32':
                return path.replace('/','\\')
            
            return path
            

        variables = dict(self.application.config.variables)
        variables.update(self.__variables)
        variables.update({
            'SGROOT':sanitize_path(game.savegame_root),
            'SAVEGAME_ROOT':sanitize_path(game.savegame_root),
            'SGDIR':sanitize_path(game.savegame_dir),
            'SAVEGAME_DIR':sanitize_path(game.savegame_dir),
            'FILENAME':sanitize_path(filename),
            'VERBOSE':self.verbose,
            'PROCESS_MAX':self.application.config.process_max
        })
            
        return variables
    
    def get_backup_args(self,game,filename):
        if not self.can_backup:
            return []    
        return shlex.split(
            Template(self.__backup_args).safe_substitute(
                self.get_variables(game,filename)))
    
    def get_restore_args(self,game,filename):
        if not self.can_restore:
            return []
        return shlex.split(
            Template(self.__restore_args).safe_substitute(
                self.get_variables(game,filename)))
    
    def do_backup(self, game, filename):
        if not self.can_backup:
            return
        
        if not os.path.isdir(game.savegame_root):
            print("!!! Savegame root directory does not exist! (Unable to extract files!)",file=sys.stderr)
            return
        
        if self.application.config.verbose:
            print("Backing up \"{game}\".".format(game=game.game_name))

        if self.change_directory:
            cwd = os.getcwd()
            os.chdir(game.savegame_root)

        cmd = [self.executable] + self.get_backup_args(game,filename)
        try:
            subprocess.run(cmd)
        except:
            if self.change_directory:
                os.chdir(cwd)

        if self.change_directory:
            os.chdir(cwd)

    def do_restore(self, game, filename):
        if not self.can_restore:
            return
        
        if self.application.config.verbose:
            print("Restore SaveGames for \"{game}\".".format(game=game.game_name))

        if not os.path.isdir(game.savegame_root):
            print("!!! Unable to restore SaveGame backup! (SaveGame root directory does not exist!)",file=sys.stderr)

        if self.change_directory:
            cwd = os.getcwd()
            os.chdir(game.savegame_root)

        cmd = [self.executable] + self.get_restore_args(game,filename)
        try:
            subprocess.run(cmd)
        except:
            if self.change_directory:
                os.chdir(cwd)
            return
        
        if self.change_directory:
            os.chdir(cwd)


def get_archivers(app):
    ret = []

    acdir = app.config.archiver_dir

    for i in os.listdir(acdir):
        filename = os.path.join(acdir,i)
        if sys.platform == 'win32':
            filename = filename.replace('/','\\')

        if os.path.isfile(filename) and filename.endswith('.archiver'):
            archiver = CommandArchiver.new_from_file(app,filename)
            if (archiver and archiver.is_valid):
                ret.append(archiver)

    return ret
