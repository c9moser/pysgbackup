# -*- coding: utf-8 -*-

#author: Christian Moser
#file: sgbackup/game.py
#module: sgbackup.game
#license: GPL

from gi.repository import GObject,GLib
from string import Template
import os
import shelve
import sys
import sgbackup
from . import error


import sgbackup
class Game(GObject.GObject):
    __name__ = "sgbackup-game-Game"
    __gsignals__ = {
        'id-changed': (GObject.SIGNAL_RUN_FIRST,None,(str,)),
        'steam-appid-changed': (GObject.SIGNAL_RUN_FIRST,None,(int,)),
        'export-gameconf': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,)),
        'export-dict': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,)),
        'backup-rename': (GObject.SIGNAL_RUN_FIRST,None,(str,str)),
        'save': (GObject.SIGNAL_RUN_FIRST,None,(GObject.TYPE_PYOBJECT,)),
        'destroy': (GObject.SIGNAL_RUN_FIRST,None,())
    }

    def __init__(self,
                 app,
                 id:str,
                 name="",
                 savegame_name="",
                 savegame_root="",
                 savegame_dir="",
                 steam_appid=None,
                 installdir="",
                 is_finished=False,
                 variables={}):
        GObject.GObject.__init__(self)

        self.__app = app
        self.__id=id
        self.__name=name
        self.__savegame_name=savegame_name
        self.__savegame_root=savegame_root
        self.__savegame_dir=savegame_dir
        self.__steam_appid=int(steam_appid)
        self.__installdir=installdir
        self.__is_finished=is_finished
        self.__variables={}
        if variables:
            self.__variables.update(variables)

    @staticmethod
    def new_from_gameconf(app,gameconf:GLib.KeyFile):
        game_id=""
        GAME_GROUP = 'game'
        VARIABLES_GROUP = 'variables'
        ERRMSG_MISSING_KEY="Missing key \"{key}\" in section \"{sect}\"!"
        if gameconf.has_group(GAME_GROUP):
            if 'id' in gameconf.get_keys(GAME_GROUP)[0]:
                game_id = gameconf.get_string(GAME_GROUP,'id')
                kwargs = {
                    'name': game_id,
                    'savegame_name': game_id
                }
            else:
                raise error.GameConfError(ERRMSG_MISSING_KEY.format(key='id',sect=GAME_GROUP))
                
            if "name" in gameconf.get_keys(GAME_GROUP)[0]:
                kwargs['name'] = gameconf.get_string(GAME_GROUP,"name")

            if  "savegameName" in gameconf.get_keys(GAME_GROUP)[0]:
                kwargs['savegame_name'] = gameconf.get_string(GAME_GROUP,"savegameName")

            if "savegameRootDirectory" in gameconf.get_keys(GAME_GROUP)[0]:
                kwargs['savegame_root'] = gameconf.get_string(GAME_GROUP,"savegameRootDirectory")
            else:
                raise error.GameConfError(ERRMSG_MISSING_KEY.format(key="savegameRootDirectory",sect=GAME_GROUP))

            if "savegameBackupDirectory" in gameconf.get_keys(GAME_GROUP)[0]:
                kwargs['savegame_dir'] = gameconf.get_string(GAME_GROUP,"savegameBackupDirectory")
            else:
                raise error.GameConfError(ERRMSG_MISSING_KEY.format(key="savegameBackupDirectory",sect=GAME_GROUP))

            if "steamAppID" in gameconf.get_keys(GAME_GROUP)[0]:
                kwargs['steam_appid'] = gameconf.get_int64(GAME_GROUP,"steamAppID")
            else:
                kwargs['steam_appid'] = 0

            if "installdir" in gameconf.get_keys(GAME_GROUP)[0]:
                kwargs['installdir'] = gameconf.get_string(GAME_GROUP,"installdir")

            if "isFinished" in gameconf.get_keys(GAME_GROUP)[0]:
                kwargs['is_finished'] = gameconf.get_boolean(GAME_GROUP,"isFinished")
            else:
                kwargs['is_finished'] = False

        else:
            error.GameConfError("Section \"{sect}\" missing in gameconf!".format(sect=GAME_GROUP))


        kwargs['variables'] = {}
        if gameconf.has_group(VARIABLES_GROUP):
            for var in gameconf.get_keys(VARIABLES_GROUP)[0]:
                kwargs['variables'][var] = gameconf.get_string(VARIABLES_GROUP,var)

        return Game(app,game_id,**kwargs)
        
    @GObject.Property
    def application(self):
        return self.__app
    
    @GObject.Property
    def is_destroyed(self):
        return (self.__app is None)
    
    @GObject.Property
    def id(self):
        return self.__id
    
    @id.setter
    def id(self,id:str):
        if not id:
            raise ValueError("\"id\" must not be an empty string!")
        old_id = self.__id
        self.__id = id
        self.emit('id-changed',old_id)
        
    @GObject.Property
    def game_id(self):
        return self.__id
    @game_id.setter
    def game_id(self,id:str):
        if not id:
            raise ValueError("\"game_id\" must not be an empty string!")
        old_id = self.__id
        self.__id = id
        self.emit('id-changed',old_id)

    @GObject.Property(str)
    def game_name(self):
        return self.__name
    @game_name.setter
    def game_name(self,name:str):
        self.__name = name

    @GObject.Property
    def name(self):
        return self.__name
    @name.setter
    def name(self,name:str):
        self.__name = name
        
    @GObject.Property
    def savegame_name(self):
        return self.__savegame_name
    @savegame_name.setter
    def savegame_name(self,sgname:str):
        if (sgname == self.savegame_name):
            return
        
        old_sgname = self.__savegame_name
        
        if (os.path.isdir(self.backup_dir)):
            os.rename(self.backup_dir,os.path.join(self.application.config.backup_dir,sgname))
            self.__savegame_name = sgname

            for i in list(os.listdir(self.backup_dir)):
                old_filename = os.path.join(self.backup_dir,i)

                if sgbackup.app.archivers.file_is_archive(old_filename) and i.startswith(old_sgname + '.'):
                    new_filename = os.path.join(self.backup_dir,i.replace(old_sgname + '.', sgname + '.'))
                    try:
                        self.emit('backup-rename',old_filename,new_filename)
                    except Exception as error:
                        print("Renaming savegame backup \"{old}\" to \"{new}\" failed! ({error})".format(
                                old=old_filename,new=new_filename,error=error),
                            file=sys.stderr)
        else:
            self.__savegame_name = sgname
    @GObject.Property
    def savegame_root_template(self):
        return self.__savegame_root
    @GObject.Property
    def savegame_root(self):
        return Template(self.__savegame_root).safe_substitute(self.variables)
    
    @savegame_root.setter
    def savegame_root(self,sgroot:str):
        self.__savegame_root = sgroot

    @GObject.Property
    def savegame_dir_template(self):
        return self.__savegame_dir
    
    @GObject.Property
    def savegame_dir(self):
        return Template(self.__savegame_dir).safe_substitute(self.variables)
    @savegame_dir.setter
    def savegame_dir(self,sgdir:str):
        self.__savegame_dir = sgdir

    @GObject.Property
    def installdir(self):
        return self.__installdir
    @installdir.setter
    def installdir(self,idir:str):
        if idir and not os.path.isabs(idir):
            raise ValueError("\"installdir\" needs to be an empty string or an absolute path!")
        self.__installdir = idir

    @GObject.Property
    def is_finished(self):
        return self.__is_finished
    @is_finished.setter
    def is_finished(self,b:bool):
        self.__is_finished = b

    @GObject.Property
    def is_active(self):
        if not self.__is_finished:
            return True
        return False
    @is_active.setter
    def is_active(self,b):
        if b:
            self.is_finished = False
        else:
            self.is_finished = True

    @GObject.Property
    def steam_appid(self):
        return self.__steam_appid
    @steam_appid.setter
    def steam_appid(self,appid):
        old_id = self.steam_appid
        if not appid:
            self.__steam_appid = None
        else:
            self.__steam_appid = int(appid)

        self.emit('steam-appid-changed',old_id)

    @GObject.Property
    def raw_variables(self):
        return self.__variables
    @GObject.Property
    def variables(self):
        vars = self.application.config.variables
        vars.update(self.__variables)
        vars['INSTALLDIR'] = self.installdir
        vars['STEAM_APPID'] = str(self.steam_appid)
        
        return vars
    @variables.setter
    def variables(self,variables:dict):
        vars = self.application.config.variables
        for key,value in variables.items():
            if key == 'INSTALLDIR':
                self.installdir = value
            elif isinstance(key,str) and isinstance(value,str):
                vars[key] = value
            else:
                raise TypeError("variable names and variable values have to be strings!")
            
        self.__variables = vars

    @GObject.Property
    def gameconf_filename(self):
        return os.path.join(self.application.config.gameconf_dir,'.'.join((self.game_id,'game')))
    
    @GObject.Property
    def backup_dir(self):
        if (sys.platform == "win32"):
            return os.path.join(self.application.config.backup_dir,self.savegame_name).replace('/','\\')
        return os.path.join(self.application.config.backup_dir,self.savegame_name)
    
    @GObject.Property
    def backups(self):
        return self.application.archivers.get_game_backups(self)
    
    @GObject.Property
    def active_backups(self):
        return self.application.archivers.get_active_game_backups(self)

    @GObject.Property    
    def finished_backups(self):
        return self.application.archivers.get_finished_game_backups(self)

    @GObject.Property
    def latest_backup(self):
        return self.application.archivers.get_latest_game_backup(self)
    
    @GObject.Property
    def latest_finished_backup(self):
        return self.application.archivers.get_latest_finished_game_backup(self)
    
    @GObject.Property
    def latest_active_backup(self):
        return self.application.archivers.get_latest_active_game_backup(self)
    
    @GObject.Property
    def kwargs(self):
        return self.__kwargs

    @GObject.Property
    def is_valid(self):
        if (self.game_id and self.game_name and self.savegame_name and self.savegame_root and self.savegame_dir):
            return True
        return False

    def get_variable(self,name:str):
        variables = self.application.config.variables
        variables.update(self.__variables)
        variables.update('INSTALLDIR',self.installdir)
        if name in variables:
            return variables[name]
        return ""
    
    def set_variable(self,name:str,value=None):
        if value is None:
            self.__variables[name] = ""
        elif isinstance(value,str):
            self.__variables[name] = value
        else:
            self.__variables[name] = str(value)

    def remove_variable(self,name:str):
        if name in self.__variables:
            del self.__variables[name]

    def export_gameconf(self):
        gameconf = GLib.KeyFile.new()
        if os.path.isfile(self.gameconf_filename):
            gameconf.load_from_file(self.gameconf_filename,0)
        self.emit('export-gameconf',gameconf)
        return gameconf
        

    def do_export_gameconf(self,gc):
        gsect='game'
        vsect='variables'

        gc.set_string(gsect,'id',self.game_id)
        gc.set_string(gsect,'name',self.game_name)
        gc.set_string(gsect,'savegameName',self.savegame_name)
        gc.set_string(gsect,'savegameRootDirectory',self.savegame_root_template)
        gc.set_string(gsect,'savegameBackupDirectory',self.savegame_dir_template)
        if (self.installdir):
            gc.set_string(gsect,'installdir',self.installdir)
        if (self.steam_appid):
            gc.set_int64(gsect,'steamAppID',self.steam_appid)
        gc.set_boolean(gsect,'isFinished',self.is_finished)

        for var,value in self.raw_variables.items():
            gc.set_string(vsect,var,value)

    def export_dict(self):
        d = {}
        self.emit('export-dict',d)
        return d

    def do_export_dict(self,d):
        d.update({
            'id': self.game_id,
            'name': self.game_name,
            'savegame_name': self.savegame_name,
            'savegame_root': self.savegame_root_template,
            'savegame_dir': self.savegame_dir_template,
            'installdir': self.installdir,
            'steam_appid': self.steam_appid,
            'is_finished': self.is_finished,
            'variables': dict(self.__variables)
        })
        d.update(self.__kwds)

    def backup(self):
        self.application.archivers.backup(self)

    def restore(self,backupfile):
        self.application.archivers.restore(self,backupfile)
        
    def do_backup_rename(self,old_filename,new_filename):
        os.rename(old_filename,new_filename)

    def save(self):
        gc = self.export_gameconf()
        self.emit('save',gc)
    # Game.save()

    def do_save(self,gc:GLib.KeyFile):
        gc.save_to_file(self.gameconf_filename)
    # Game.do_save()

    def destroy(self):
        self.emit('destroy')

    def do_destroy(self):
        self.__app = None

    def do_id_changed(self,old_id):
        pass

    def do_steam_appid_changed(self,old_id):
        pass
#Game class
