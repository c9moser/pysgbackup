#-*- coding:utf-8 -*-

from sgbackup import config,backup
import os
from string import Template

class Game(object):
    def __init__(self,game_id,name,sg_name,sg_root,sg_dir,id=0,final_backup=False,steam_appid=None,variables={}):
        object.__init__(self)
        
        if id:
            self.id = id
        else:
            self.__id=0
            
        self.game_id = game_id
        self.name = name
        self.savegame_name = sg_name
        self.savegame_root = sg_root
        self.savegame_dir = sg_dir
        self.final_backup = final_backup
        self.steam_appid=steam_appid
        self.__variables = dict(variables)
        
    @property
    def id(self):
        return self.__id
        
    @id.setter
    def id(self,x):
        if not isinstance(x,int):
            raise TypeError("'id' is not an integer!")
        if x <= 0:
            raise ValueError("'id' must be greater than 0!")
        self.__id = x
        
    @property
    def game_id(self):
        return self.__game_id
        
    @game_id.setter
    def game_id(self,x):
        if not isinstance(x,str):
            raise TypeError("'game_id' is not a string!")
        if len(x) == 0:
            raise ValueError("'game_id' must not be an empty string!")
        if len(x) > 64:
            raise ValueError("'game_id' too long!")
        self.__game_id = x
        
        
    @property
    def name(self):
        return self.__name   
        
    @name.setter
    def name(self,x):
        if not isinstance(x, str):
            raise TypeError("'name' is not a string!")
        if len(x) == 0:
            raise ValueError("'name' must not be an empty string!")
        if len(x) > 512:
            raise ValueError("'name' too long!")
        self.__name = x
        
    @property
    def savegame_name(self):
        return self.__sg_name   
        
    @savegame_name.setter
    def savegame_name(self, x):
        if not x:
            self.__sg_name = None
            return
        
        if not isinstance(x,str):
            raise TypeError("'savegame_name' is not a string!")
        if len(x) > 256:
            raise ValueError("'savegame_name' too long!")
        self.__sg_name = x
            
    @property
    def raw_savegame_root(self):
        return self.__sg_root
        
    @property
    def savegame_root(self):
        return os.path.normpath(Template(self.__sg_root).substitute(self.variables))
        
    
    @savegame_root.setter
    def savegame_root(self,x):
        if not isinstance(x,str):
            raise TypeError("'savegame_root' is not a string!")
        self.__sg_root = x
        
    @property
    def raw_savegame_dir(self):
        return self.__sg_dir

    @property
    def savegame_dir(self):
        return os.path.normpath(Template(self.__sg_dir).substitute(self.variables))
        
    @savegame_dir.setter
    def savegame_dir(self,x):
        if not isinstance(x,str):
            raise TypeError("'savegame_dir' is not a string!")
        self.__sg_dir=x
       
    @property
    def final_backup(self):
        return self.__final_backup
        
    @final_backup.setter
    def final_backup(self,x):
        if x:
            self.__final_backup = True
        else:
            self.__final_backup = False
            
    @property
    def steam_appid(self):
        if self.__steam_appid:
            return self.__steam_appid
        else:
            return ""
            
    @steam_appid.setter
    def steam_appid(self,appid):
        self.__steam_appid = appid
        
    @property
    def raw_variables(self):
        return self.__variables
        
    @property
    def variables(self):
        v = config.get_template_vars()
        v.update(self.__variables)
        
        return v
         
# Game class

class GameConf(object):
    def __init__(self,filename,checksum,user_file=False,game_id=""):
        if not os.path.isabs(filename):
            raise TypeError('\'filename\' needs to ba an absolute path!')
        self.__filename = filename
        
        if not game_id:
            self.__game_id = os.path.splitext(os.path.basename(filename))[0]
        else:
            self.__game_id = game_id
            
        self.checksum=checksum
        self.user_file=user_file
        
    @property
    def game_id(self):
        return self.__game_id

    @game_id.setter
    def game_id(self,gid):
        self.__game_id = gid
        
    @property
    def filename(self):
        return self.__filename
    
    @property
    def checksum(self):
        return self.__checksum

    @checksum.setter
    def checksum(self,cksum):
        self.__checksum=cksum
        
    @property
    def user_file(self):
        return self.__user_file
        
    @user_file.setter
    def user_file(self,x):
        if (x):
            self.__user_file=True
        else:
            self.__user_file=False
            


