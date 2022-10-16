#-*- coding:utf-8 -*-
################################################################################
# sgbackup
#   Copyright (C) 2022,  Christian Moser
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
################################################################################

from ..commands import COMMANDS
from ..config import CONFIG,add_config

class Plugin(object):
    def __init__(self,name,
                 description='',
                 commands={},
                 config={},
                 version='.'.join((str(i) for i in CONFIG['version'])),
                 check_version_callback=None,
                 update_callback=None,
                 config_parse_callback=None,
                 config_write_callback=None,
                 config_set_callback=None,
                 config_show_callback=None,
                 config_values_callback=None,
                 backup_callback=None,
                 restore_callback=None,
                 delete_backup_callback=None,
                 delete_savegames_callback=None,
                 spec={},
                 **kwargs):
        object.__init__(self)
        
        self.__name = name
        self.__version = version
        self.__enabled = False
        self.__description = description
        self.__commands = commands
        self.__check_version_callback = check_version_callback
        self.__update_callback = update_callback
        self.__config_parse_callback = config_parse_callback
        self.__config_write_callback = config_write_callback
        self.__config_set_callback = config_set_callback
        self.__config_show_callback = config_show_callback
        self.__config_values_callback = config_values_callback
        self.__backup_callback = backup_callback
        self.__restore_callback = restore_callback
        self.__delete_backup_callback = delete_backup_callback
        self.__delete_savegames_callback = delete_savegames_callback

        self._init_config(config)

    def __del__(self):
        if self.enabled:
            self.disable()
            
    def _init_config(self,conf):
        global_config = False
        local_config = False
        section = ""
        if 'global' in conf:
            global_config = conf['global']
        if 'local' in conf:
            local_config = conf['local']
        if 'section' in conf:
            section = conf['section']
        
        if 'values' in conf:
            for i in conf['values']:  
                cfg = conf['values'][i]
                if not 'global' in cfg:
                    cfg['global'] = global_config
                if not 'local' in cfg:
                    cfg['local'] = local_config
                
                if (section and 'section' not in cfg and 'option' in cfg):
                    cfg['section']=section
                
                add_config(i,cfg)
            
        if self.config_parse_callback:
            CONFIG['config-parse-callbacks'].append(self.config_parse)
        if self.config_write_callback:
            CONFIG['config-write-callbacks'].append(self.config_write)
        if self.config_set_callback:
            CONFIG['config-set-callbacks'].append(self.config_set)
        if self.config_show_callback:
            CONFIG['config-show-callbacks'].append(self.config_show)
        if self.config_values_callback:
            CONFIG['config-values-callbacks'].append(self.config_values)
            
    @staticmethod
    def new_from_dict(spec):
        if 'name' not in spec:
            return None
            
        name = spec['name']
        kwargs={'spec':{}}
        
        for k in spec.keys():
            if k == 'name':
                continue
            elif k == 'description':
                kwargs['description'] = spec[k]
            elif k == 'commands':
                kwargs['commands'] = spec[k]
            elif k == 'config':
                kwargs['config'] = spec[k]
            elif k == 'version':
                kwargs['version'] = spec[k]
            elif k == 'update-callback' or k == 'update_callback':
                kwargs['update_callback'] = spec[k]
            elif k == 'config-parse-callback' or k == 'config_parse_callback':
                kwargs['config_parse_callback'] = spec[k]
            elif k == 'config-write-callback' or k == 'config_write_callback':
                kwargs['config_write_callback'] = spec[k]
            elif k == 'config-set-callback' or k == 'config_set_callback':
                kwargs['config_set_callback'] = spec[k]
            elif k == 'backup-callback' or k == 'backup_callback':
                kwargs['backup_callback'] = spec[k]
            elif k == 'restore-callback' or k == 'restore_callback':
                kwargs['restore_callback'] = spec[k]
            elif k == 'delete-backup-callback' or k == 'delete_backup_callback':
                kwargs['delete_backup_callback'] = spec[k]
            elif k == 'delete-savegames-callback' or k == 'delete_savegames_callback':
                kwargs['delete_savegames_callback'] = spec[k]
            elif k == 'config-show-callback' or k == 'config_show_callback':
                kwargs['config_show_callback'] = spec[k]
            elif k == 'config-values-callback' or k == 'config_values_callback':
                kwargs['config_values_callback'] = spec[k]
            else:
                kwargs['spec'][k] = spec[k]
        return Plugin(name,**kwargs)
        
    @property
    def name(self):
        return self.__name
    @property
    def version(self):
        return self.__version
        
    @property
    def commands(self):
        return self.__commands
        
    @property
    def description(self):
        return self.__description
        
    @property
    def enabled(self):
        return self.__enabled     
    
    @property
    def check_version_callback(self):
        return self.__check_version_callback
        
    @property
    def config_parse_callback(self):
        return self.__config_parse_callback
        
    @property
    def config_write_callback(self):
        return self.__config_write_callback
        
    @property
    def config_set_callback(self):
        return self.__config_set_callback
        
    @property
    def config_show_callback(self):
        return self.__config_show_callback
        
    @property
    def config_values_callback(self):
        return self.__config_values_callback
        
    @property
    def update_callback(self):
        return self.__update_callback
        
    @property
    def backup_callback(self):
        return self.__backup_callback
        
    @property
    def restore_callback(self):
        return self.__restore_callback
        
    @property
    def delete_savegames_callback(self):
        return self.__delete_savegames_callback
        
    @property
    def delete_backup_callback(self):
        return self.__delete_backup_callback
        
    def config_parse(self,cparser):
        callback = self.config_parse_callback
        if callback:
            callback(cparser)
            
    def config_write(self,cparser,global_config):
        callback = self.config_write_callback
        if callback:
            callback(cparser,global_config)
            
    def config_set(self,key,value):
        callback = self.config_set_callback
        if callback:
            callback(key,value)
        
    def config_show(self,key):
        callback = self.config_show_callback
        if callback:
            callback(key)
            
    def config_values(self,global_config=False):
        callback = self.config_values_callback
        if callback:
            callback(global_config)
        
    def backup(self,db,game,filename):
        callback = self.backup_callback
        if callback:
            callback(db,game,filename)
    
    def check_version(self,version):
        if self.check_version_callback:
            return self.check_version_callback(version)
        
        new_version = self.version.split('.')
        old_version = version.split('.')
        if len(new_version) >= 3 and len(old_version) >= 3:
            return (old_version[0] == new_version[0] 
                    and old_version[1] == new_version[1]
                    and old_version[2] >= new_version[2])
        elif len(new_version) >= 2 and len(old_version) >= 2:
            return (old_version[0] == new_version[0] and old_version[1] >= new_version[1])
        elif len(new_version) >= 1 and len(old_version) >= 1:
            return (old_version[0] >= new_version[0])
        
    def update(self,db,version=None):
        db_plugin = db.get_plugin(self.name)
        if not db_plugin:
            return
        if not version:
            version = db_plugin['version']
        callback = self.update_callback
        if callback:
            callback(db,version)
            
        db.add_plugin(self)
    
    
    def delete_backup(self,db,game,filename):
        callback = self.delete_backup_callback
        if callback:
            callback(db,game,filename)
            
    def delete_savegames(self,db,game):
        callback = self.delete_savegames_callback
        if callback:
            callback(db,game)
            
    def restore(self,db,game,filename):
        callback = self.restore_callback
        if callback:
            callback(db,game,filename)
            
    def enable(self):
        for cmd,value in self.commands.items():
            COMMANDS[cmd] = value
        
        if self.backup_callback:
            CONFIG['backup-callbacks'][self.name]=self.backup
        
        if self.restore_callback:
            CONFIG['restore-callbacks'][self.name]=self.restore
        
        if self.delete_backup_callback:
            CONFIG['delete-backup-callbacks'][self.name]=self.delete_backup
            
        if self.delete_savegames_callback:
            CONFIG['delete-savegames-callbacks'][self.name]=self.delete_savegame
        
        self.__enabled = True
        
    def disable(self):
        if self.__enabled:
            for cmd in self.commands.keys():
                del COMMANDS[cmd]
                
        if self.name in CONFIG['backup-callbacks']:
            del CONFIG['backup-callbacks'][self.name]
            
        if self.name in CONFIG['restore-callbacks']:
            del CONFIG['restore-callbacks'][self.name]
            
        if self.name in CONFIG['delete-backup-callbacks']:
            del CONFIG['delete-backup-callbacks'][self.name]
            
        if self.name in CONFIG['delete-savegames-callbacks']:
            del CONFIG['delete-savegames-callbacks'][self.name]
            
        self.__enabled = False
        
        
