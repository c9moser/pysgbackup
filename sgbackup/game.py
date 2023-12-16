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
    """
    The :class:`Game`-class holds the game-data required for 
    backup and restore operations. It also provides an backup
    and restore functions.

    :param app: The application the game is registered to.
    :type app: :class:`sgbackup.application.Application`
    :param id: The game id. This parameter is used to lookup the
        game.
    :type id: `str`
    :param name: The name of the game.
    :type name: `str`
    :param savegame_name: The name used in backup-files.
    :type savegame_name: `str`
    :param savegame_root: The root directory for backups.
        This is an template string that can contain variables and 
        should result in an absolute path after applying the variables.
        
        When restoring a backup the *savegame_root* 
        directory is not created!
    :type savegame_root: `str`
    :param savegame_dir: The directory to backup. This is a template string
        that should result in a realtive path originating from the *savegame_root* 
        directory after applying the variables.

        When restoring a backup the *savegame_dir* path originating from 
        *savegame_root* is created!
    :type savegame_dir: `str`
    :param steam_appid: The *Steam AppID* of the game. If the game is not a
        *Steam* game set this parameter to `None`, else use an positive integer
        representing the *AppID*.
    :type steam_appid: `None` or `int`.
    :param installdir: The Game installation directory. You can set this parameter
        to an empty string if not needed.
    :type installdir: `str`
    :param is_finished: `True` if the game is finished, `False` otherwise. Set this
        parameter to `False` for new created games.
    :type is_finished: `bool`
    :param variables: Variables that can be used in *savegame_dir* and *savegame_root*.

        This parameter should be `None` if not used or a dictionary with the variable name
        as keys and the variable value as string values.
    :type variables: `dict`

    SIGNALS
    ^^^^^^^
    * *backup-rename*
    * *destroy*
    * *export-gameconf*
    * *export-dict*
    * *id-changed*
    * *save*
    * *steam-appid-changed*
    """
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
                 variables=None,
                 **kwargs):
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

        if not kwargs:
            self.__kwargs = {}
        else:
            self.__kwargs = kwargs

    @staticmethod
    def new_from_gameconf(app,gameconf:GLib.KeyFile):
        """
        Create a Game from a game configuration.

        If parsing fails, a :class:`sgbackup.error.GameConfError` is raised.

        :param app: The application the game will be registered to.
        :type app: :class:`sgbackup.application.Application`
        :param gemconf: The gameconf to parse. This is an GLib.KeyFile instance.
        :type gameconf: :class:`GLib.KeyFile`
        :returns: A Game instance if the gameconf is successfully parsed.
        """
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
        """
        *(read only)* -
        The application the Game is registered to.

        :type: :class:`sgbackup.application.Application`
        """
        return self.__app
    
    @GObject.Property
    def is_destroyed(self):
        """
        (*read only)* -
        `True` if the class has been destroyed.

        :type: `bool`
        """
        return (self.__app is None)
    
    @GObject.Property
    def id(self):
        """
        *(read write)* - 
        The ID of the game. The ID is used for looking up games.

        :type: `str`
        """
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
        """
        *(read write)* -
        The id of the game. It is the same as the `id` property.

        :type: `str`
        """
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
        """
        *(read write)* -
        The name of the game. This is the same as the `name` property.

        :type: `str`
        """
        return self.__name
    @game_name.setter
    def game_name(self,name:str):
        self.__name = name

    @GObject.Property
    def name(self):
        """
        *(read write)* -
        The name of the game. This is the same as the `game_name` property.

        :type: `str`
        """
        return self.__name
    @name.setter
    def name(self,name:str):
        self.__name = name
        
    @GObject.Property
    def savegame_name(self):
        """
        *(read write)* - 
        The savegame name of a game. The `savegame_name` is used as the directory
        name for savegame backups and as the name in the generated savegame-backup-file.

        It is a good idea not to have any spaces in the filename. Use CamelCase or underscores
        '_' inestad of spaces.

        :type: `str`
        """
        return self.__savegame_name
    @savegame_name.setter
    def savegame_name(self,sgname:str):
        if (sgname == self.savegame_name):
            return
        
        new_backup_dir = os.path.join(self.application.config.backup_dir,sgname)
        if os.path.exists(new_backup_dir):
            raise FileExistsError("\"{directory}\" already exists!".format(directory=new_backup_dir))

        old_sgname = self.__savegame_name
        old_backup_dir = self.backup_dir
        old_backups = self.backups
        self.__savegame_name = sgname
        if (os.path.isdir(old_backup_dir)):
            for i in old_backups:
                dirname,old_filename = os.path.split(i)
                filename = old_filename.replace(old_sgname + ".", sgname + ".")
                self.emit('backup-rename',os.path.join(dirname,old_filename),os.path.join(dirname,filename))
                
            os.rename(old_backup_dir,self.backup_dir)
        
    @GObject.Property
    def savegame_root_template(self):
        """
        *(read only)* -
        The unexpanded `savegame_root` string.

        You can set a template-string using the `savegame_root` property.

        :type: `str`
        """
        return self.__savegame_root
    @GObject.Property
    def savegame_root(self):
        """
        *(read write)* -
        Get the expanded `savegame_root` string. This should be an
        absolute path.

        You can set template strings using this property.

        :type: `str`
        """
        return Template(self.__savegame_root).safe_substitute(self.variables)
    
    @savegame_root.setter
    def savegame_root(self,sgroot:str):
        self.__savegame_root = sgroot

    @GObject.Property
    def savegame_dir_template(self):
        """
        *(read only)* -
        The unexpanded savegame direcotry as a raw template string.

        To set the template string use the `savegame_dir` property.

        :type: `str`
        """
        return self.__savegame_dir
    
    @GObject.Property
    def savegame_dir(self):
        """
        *(read write)*
        The savegame directory after variable expansion.

        To set a template string use this property. Variable expansion only happens
        on reding this property.

        The `savegame_dir` should result in a relative path originating from `savegame_root`.

        :type: `str`
        """
        return Template(self.__savegame_dir).safe_substitute(self.variables)
    @savegame_dir.setter
    def savegame_dir(self,sgdir:str):
        self.__savegame_dir = sgdir

    @GObject.Property
    def installdir(self):
        """
        *(read write)* -
        The game installation directory. This property is optional.
        When set it should result in an absolute path.

        :type: `str`
        """
        return self.__installdir
    @installdir.setter
    def installdir(self,idir:str):
        if idir and not os.path.isabs(idir):
            raise ValueError("\"installdir\" needs to be an empty string or an absolute path!")
        self.__installdir = idir

    @GObject.Property
    def is_finished(self):
        """
        *(read write)* -
        `True` if the game is finished. This property can be used for payed-through
        games to exclude then when backing up active games.

        :type: `bool`
        """
        return self.__is_finished
    @is_finished.setter
    def is_finished(self,b:bool):
        self.__is_finished = b

    @GObject.Property
    def is_active(self):
        """
        *(read write)* -
        `True` if the game is active. This property is the opposite of the 
        `is_finished` proporty.

        :type: `bool`
        """
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
        """
        *(read write)* -
        The Steam AppID of a game. This is an optional property
        and should only be set for Steam-games.

        If this is not a steam game `0` is returned.

        :type: `int`
        """
        if not self.__steam_appid:
            return 0
        
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
        """
        *(read only)*
        The variables set for the game. They are not extended by 
        environment variables and global variables.

        This property returns a dictionary where the keys are variable names
        and the vaules are variable value strings.

        To set a variable dictionary use the `variables` property.

        :type: `dict`
        """
        return self.__variables
    @GObject.Property
    def variables(self):
        """
        *(read write)* -
        Game variables. This property returns the variables
        used for template expansion. It extends the game-variables
        with environment variables and global variables. It also
        adds the variables *INSTALLDIR* and *STEAM_APPID*.

        When setting a variable dict use only game variables.

        :type: `dict`
        """
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
        """
        *(read only)* -
        The generated backup directory of the game.

        :type: `str`
        """
        if (sys.platform == "win32"):
            return os.path.join(self.application.config.backup_dir,self.savegame_name).replace('/','\\')
        return os.path.join(self.application.config.backup_dir,self.savegame_name)
    
    @GObject.Property
    def backups(self):
        """
        *(read only)* -
        Get all backups for the game.
        This property returns a list of all backups
        as a `list` of absolute paths.

        :type: `list(str)`
        """
        return self.application.archivers.get_game_backups(self)
    
    @GObject.Property
    def active_backups(self):
        """
        *(read only)* -
        Get a list of all active backups for the game.
        This property returns a list of all active backups for the game
        as a `list` of absolute paths.

        :type: `list(str)`
        """
        return self.application.archivers.get_active_game_backups(self)

    @GObject.Property    
    def finished_backups(self):
        """
        *(read only)* -
        Get a list of all finished backups for the game.
        This property returns a list of all finished backups for the game
        as a `list` of absolute paths.

        :type: `list(str)`
        """
        return self.application.archivers.get_finished_game_backups(self)

    @GObject.Property
    def latest_backup(self):
        """
        *(read only)* -
        Get the latest backup for the game as an absolute path.

        :type: `str`
        """
        return self.application.archivers.get_latest_game_backup(self)
    
    @GObject.Property
    def latest_finished_backup(self):
        """
        *(read only)* -
        Get the latest finished backup for the game as an absolute path.

        :type: `str`
        """
        return self.application.archivers.get_latest_finished_game_backup(self)
    
    @GObject.Property
    def latest_active_backup(self):
        """
        *(read only)*
        Get the latest active backup for the game as an absolute path.

        :type: `str`
        """
        return self.application.archivers.get_latest_active_game_backup(self)
    
    @GObject.Property
    def kwargs(self):
        return self.__kwargs

    @GObject.Property
    def is_valid(self):
        """
        *(read only)* -
        Validate the game if it can create and restore backups.

        :type: `bool`
        """
        if (self.game_id and self.game_name and self.savegame_name and self.savegame_root and self.savegame_dir):
            return True
        return False

    def get_variable(self,name:str):
        """
        Get a single variable from the variables `dict`.
        If the variable does not exist, an empty string is returned.
        
        :param name: The variable name.
        :type name: `str`
        :returns: A `str` containing the variable value.
        """
        variables = self.application.config.variables
        variables.update(self.__variables)
        variables.update('INSTALLDIR',self.installdir)
        if name in variables:
            return variables[name]
        return ""
    
    def set_variable(self,name:str,value=None):
        """
        Set a variable. This method is preffered over settings
        the variables as a `dict` directly.

        If the variable exists it is overwritten with the new value.

        :param name: The variable name.
        :type name: `str`
        :param value: The variable value. If the value is `None`
            an empty variable is set.
        :type value: `str` or `None`.
        """
        if value is None:
            self.__variables[name] = ""
        elif isinstance(value,str):
            self.__variables[name] = value
        else:
            self.__variables[name] = str(value)

    def remove_variable(self,name:str):
        """
        Remove a variable from the variables `dict`.
        If the variable does not exist this mehtod does nothing.

        :param name: The variable name to remove.
        :type name: `str`
        """
        if name in self.__variables:
            del self.__variables[name]

    def export_gameconf(self):
        """
        Export the gameconf settings to a *.game* file.

        :returns: A `GLib.KeyFile` object containing the actual 
            game configutration.
        """
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
