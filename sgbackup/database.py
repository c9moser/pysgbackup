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

from . import config, games, plugins

import sqlite3
import os

class Database:
    DB_ENGINE="sqlite3"
        
    def __init__(self,db=None, connect=True):
        self.__db = None
        
        if not db:
            self.__db_file = config.CONFIG["database"];
        else:
            self.__db_file = db
            
        if not os.path.isfile(self.db_file):
            if (os.path.isdir(self.db_file)):
                raise ValueError("Database file '{0}' is a directory!".format(self.db_file))
            if (os.path.exists(self.db_file)):
                os.unlink(self.db_file)
            self.__needs_creation = True
        else:
            self.__needs_creation = False
        
        if (connect):
            self._connect()
    # __init__()
        
    def __del__(self):
        self.close()
    # del()
        
    @property
    def _db(self):
        return self.__db
    # property _db
        
    @property
    def db_file(self):
        return self.__db_file
    # property db_file
        
    @property
    def needs_creation(self):
        return self.__needs_creation
    # property needs_creation
        
    def _connect(self):
        self.__db = sqlite3.connect(self.db_file)
        if (self.needs_creation):
            with open(config.CONFIG['database.create-sql'],'r') as sql_file:
                self._db.executescript(sql_file.read())
                self.__needs_creation=False
    # _connect()

        
    def close(self):
        if self.DB_ENGINE == "sqlite3" and self.__db:
            self.__db.close()
            self.__db = None
    # close()
            

    def _bool_to_db(self,x):
        if (x):
            return 'Y'
        return 'N'
    # _bool_to_db()
        
    def _db_to_bool(self,x):
        if (x.upper() == 'Y'):
            return True
        elif (x.upper() == 'N'):
            return False
            
        raise ValueError("'db-bool' must be 'Y' or 'N'!")
    # _db_to_bool()
        
        
    def list_games(self):
        """
        return a list of game_id,name tuples.
        """
        
        sql = "SELECT game_id,name FROM games ORDER BY game_id;"
        ret = []
        
        cur = self._db.cursor()
        cur.execute(sql)
        
        for row in cur:
            ret.append((row[0],row[1]))
            
        return ret
    # list_games()
    
    def list_game_ids(self):
        sql = "SELECT game_id FROM games ORDER BY game_id;"
        ret =[]
        
        cur = self._db.cursor()
        cur.execute(sql)
        
        for row in cur:
            ret.append(row[0])
            
        return ret
    # list_game_ids
    
    def list_game_names(self):
        sql = "SELECT name FROM games ORDER BY name;"
        ret = []
        
        cur = self._db.cursor()
        cur.execute(sql)
        
        for row in cur:
            ret.append(row[0])
            
        return ret
    # list_game_names()
        
        
    def has_game(self,game_id):
        sql = "SELECT id FROM games WHERE game_id=?;"
        cur = self._db.cursor()
        
        cur.execute(sql,(game_id,));
        row = cur.fetchone()
        if row and row[0]:
            return True
        return False
        
    def get_game(self,game_id):
        sql = "SELECT id,name,savegame_name,savegame_root,savegame_dir,final_backup,steam_appid FROM games WHERE game_id=?;"
        var_sql="SELECT name,value FROM game_variables WHERE game=?;"
        
        ret = None
        cur = self._db.cursor()
        cur.execute(sql,(game_id,))
        row = cur.fetchone()
        
        if row:
            cur.execute(var_sql,(row[0],))
            var = {}
            for i in cur:
                var[i[0]] = i[1]
                
            ret = games.Game(game_id,row[1],row[2],row[3],row[4],row[0],self._db_to_bool(row[5]),variables=var,steam_appid=row[6])
            
        return ret
    # get_game()
    
    def get_game_by_steam_appid(self,appid):
        sql = "SELECT id,game_id,name,savegame_name,savegame_root,savegame_dir,final_backup FROM games WHERE steam_appid=?;"
        var_sql="SELECT name,value FROM game_variables WHERE game=?;"
        
        ret = None
        cur = self._db.cursor()
        cur.execute(sql,(appid,))
        row = cur.fetchone()
        
        if row:
            cur.execute(var_sql,(row[0],))
            var={}
            for i in cur:
                var[i[0]] = i[1]
                
            ret = games.Game(row[1],row[2],row[3],row[4],row[5],row[0],self._db_to_bool(row[6]),variables=var,steam_appid=appid)
        return ret
    
    def get_gameconf(self,game_id):
        sql = "SELECT filename,checksum,user_file FROM gameconf WHERE game=(SELECT id FROM games WHERE game_id=?);"
        
        ret = []
        cur = self._db.cursor()
        cur.execute(sql,(game_id,))
        
        for row in cur:
            gc = games.GameConf(row[0],row[1],row[2],game_id)
            ret.append(gc)
            
        return ret        
    # get_gameconf()
        
    def get_gameconf_by_filename(self,filename):
        sql = """SELECT t2.game_id,t1.checksum,t1.user_file 
            FROM gameconf AS t1 JOIN games AS t2 ON t1.game=t2.id 
            WHERE t1.filename=?;"""
    
        ret = None
        fn = os.path.normpath(filename)
        cur = self._db.cursor()
        cur.execute(sql,(fn,))
        
        row = cur.fetchone();
        
        if row:
            ret = games.GameConf(fn,row[1],row[2],row[0])
        
        return ret
    # get_gameconf_by_filename()
        
    def add_gameconf(self,filename,game):
        if not game.id:
            game = self.get_game(game.game_id)
        assert(game)
            
        fn = os.path.normpath(filename)
        gc = self.get_gameconf_by_filename(fn)
        
        new_gc = games.get_gameconf_data_by_filename(fn,game.game_id)
        
        if gc:
            sql="UPDATE gameconf SET checksum=?,user_file=? WHERE filename=?;"
            sql_args=(new_gc.checksum,self._bool_to_db(new_gc.user_file),fn)
        else:
            sql="INSERT INTO gameconf (game,filename,checksum,user_file) VALUES (?,?,?,?);"
            sql_args=(game.id,fn,new_gc.checksum,self._bool_to_db(new_gc.user_file))
            
        cur = self._db.cursor()
        cur.execute(sql,sql_args)
        self._db.commit()
    # add_gameconf()
        
    def delete_gameconf(self,filename):
        sql="DELETE FROM gameconf WHERE filename=?;"
        
        cur = self._db.cursor()
        cur.execute(sql,(os.path.normpath(filename),))
        self._db.commit()
    # delete_gameconf()
        
    def add_game_variables(self,game):
        def _has_game_variable(game,name):
            cur = self._db.cursor()
            cur.execute('SELECT id FROM game_variables WHERE game=? AND name=?;',(game.id,name))
            row = cur.fetchone()
            if row and row[0] > 0:
                return True
            return False
        # _has_game_variable()
            
        if game.id > 0:
            g = game
        else:
            g = self.get_game(game.game_id)
            
        if game.raw_variables:
            cur = self._db.cursor()
            cur.execute('SELECT name FROM game_variables WHERE game=?;',(g.id,))
            for row in cur:
                if row[0] not in game.raw_variables:
                    cur2 = self._db.cursor()
                    cur2.execute('DELETE FROM game_variables WHERE game=? AND name=?;',(g.id,row[0]))
            
            for k,v in game.raw_variables.items():
                if _has_game_variable(g,k):
                    sql = "UPDATE game_variables SET value=? WHERE game=? AND name=?;"
                    sql_args = (v,g.id,k)
                else:
                    sql = "INSERT INTO game_variables (game,name,value) VALUES (?,?,?);"
                    sql_args = (g.id,k,v)
                cur.execute(sql,sql_args)
        self._db.commit()
    # add_game_variables()
        
    def add_game(self,game,gameconf=[]):
        def _has_game_variable(game,varname):
            sql = 'SELECT id FROM game_variables WHERE game=? AND name=?;'
            cur = self._db.cursor()
            cur.execute(sql,(game.id,varname))
            row = cur.fetchone()
            if row and row[0] > 0:
                return True
            return False
        # _has_game_variable()
        
        if game.id:
            sql_args = (
                game.game_id,
                game.name,
                game.savegame_name,
                game.raw_savegame_root,
                game.raw_savegame_dir,
                self._bool_to_db(game.final_backup),
                game.steam_appid,
                game.id)
            sql = "UPDATE games SET game_id=?,name=?,savegame_name=?,savegame_root=?,savegame_dir=?,final_backup=?,steam_appid=? WHERE id=?;"
        else:
            g=self.get_game(game.game_id)
            if (g):
                if (game.final_backup or g.final_backup):
                    final_backup=True
                else:
                    final_backup=False
                game.id = g.id 
                sql_args = (
                    game.name,
                    game.savegame_name,
                    game.raw_savegame_root,
                    game.raw_savegame_dir,
                    self._bool_to_db(final_backup),
                    game.steam_appid,
                    game.game_id)
                sql = "UPDATE games SET name=?,savegame_name=?,savegame_root=?,savegame_dir=?,final_backup=?,steam_appid=? WHERE game_id=?;"
            else:
                sql_args = (
                    game.game_id,
                    game.name,
                    game.savegame_name,
                    game.raw_savegame_root,
                    game.raw_savegame_dir,
                    self._bool_to_db(game.final_backup),
                    game.steam_appid)
                sql = "INSERT INTO games (game_id,name,savegame_name,savegame_root,savegame_dir,final_backup,steam_appid) VALUES(?,?,?,?,?,?,?);"

        cur = self._db.cursor()
        cur.execute(sql,sql_args)
        self._db.commit()
        
        if game.raw_variables:
            self.add_game_variables(game)
            
        g = self.get_game(game.game_id)
                
        for i in gameconf:
            self.add_gameconf(i.filename,g)
    # add_game()
    
    
    def delete_game(self,game_id):
        sql = "DELETE FROM games WHERE game_id=?;"
        
        for gc in self.get_gameconf(game_id):
            self.delete_gameconf(gc.filename)
        
        cur = self._db.cursor()
        cur.execute(sql,(game_id,))
        self._db.commit()
    # delete_game()
    
    def list_plugins(self):
        ret = []
        sql = "SELECT id,name,version,enabled FROM plugins ORDER BY name;"
        
        cur = self._db.cursor()
        cur.execute(sql)
        for row in cur:
            ret.append({'id':int(row[0]),'name':row[1],'version':row[2],'enabled':self._db_to_bool(row[3])})
            
        return ret
    # list_plugins()
    
    def get_plugin(self,plugin):
        if isinstance(plugin,plugins.Plugin):
            name = plugin.name
        else:
            name = plugin
        ret = None
        sql = "SELECT id,name,version,enabled FROM plugins WHERE name=?;"
        
        cur = self._db.cursor()
        cur.execute(sql,(name,))
        row = cur.fetchone()
        if row:
            ret = {'id':int(row[0]),'name':row[1],'version':row[2],'enabled': self._db_to_bool(row[3])}
            
        return ret
        
    def add_plugin(self,plugin):
        if not isinstance(plugin,plugins.Plugin):
            raise TypeError('plugin')
            
        sql = "INSERT INTO plugins(name,version) VALUES (?,?);"
        cur = self._db.cursor()
        cur.execute(sql,(plugin.name,plugin.version))
        self._db.commit()
        
    def has_plugin(self,plugin):
        if isinstance(plugin,plugins.Plugin):
            name = plugin.name
        else:
            name = plugin
            
        sql = "SELECT id FROM plugins WHERE name=?;"
        cur = self._db.cursor()
        cur.execute(sql,(name,))
        
        row = cur.fetchone()
        if (row and row[0]):
            return True
        return False
    # has_plugin
        
    def delete_plugin(self,plugin):
        if isinstance(plugin,plugins.Plugin):
            name = plugin.name
        else:
            name = plugin
            
        sql = "DELETE FROM plugins WHERE name=?;"
        
        cur = self._db.cursor()
        cur.execute(sql,(name,))
        self._db.commit()
        
    def enable_plugin(self,plugin):
        if isinstance(plugin,plugins.Plugin):
            name = plugin.name
        else:
            name = plugin
            
        sql = "UPDATE plugins SET enabled='Y' WHERE name=?;"
        cur = self._db.cursor()
        cur.execute(sql,(name,))
        self._db.commit()
    # enable_plugin()
        
    def disable_plugin(self,plugin):
        if isinstance(plugin,plugins.Plugin):
            name = plugin.name
        else: 
            name = plugin
            
        sql = "UPDATE plugins SET enabled='N' WHERE name=?;"
        cur = self._db.cursor()
        cur.execute(sql,(name,))
        self._db.commit()
    # disable_plugin()
    
    def update_plugin(self,plugin):
        if not isinstance(plugin,plugins.Plugin):
            raise TypeError('plugin')
            
        sql = "UPDATE plugins SET version=? WHERE name=?;"
        cur = self._db.cursor()
        cur.execute(sql,(plugin.version,plugin.name))
        self._db.commit()
    # update_plugin()
    
    def add_game_backup(self,game,filename,checksum,hash):
        if (isinstance(game,str)):
            g = self.get_game(game)
        elif (isinstance(game,games.Game)):
            g = self.get_game(game.game_id)
        else:
            raise TypeError('game')
        if not g:
            raise LookupError('game')
            
        sql='INSERT INTO filelist(game,filename,checksum,hash) VALUES (?,?,?,?);'
        cur = self._db.cursor()
        
        cur.execute(sql,(game.id,os.path.basename(filename),checksum,hash))
        self._db.commit()  
    # add_game_backup
    
    def add_game_backup_extrafile(self,game,filename,extrafile,use_ftp=False):
        backup = self.get_game_backup(game,filename)
        if not backup:
            raise LookupError('filename')
            
        sql = "INSERT INTO filelist_extrafiles (file,filename,use_ftp) VALUES (?,?,?);"
        cur = self._db.cursor()
        cur.execute(sql,(backup['id'],os.path.basename(extrafile),self._bool_to_db(use_ftp)))
        self._db.commit()
    # add_game_backup_extrafile()    
    
    def get_game_backups(self,game):
        if isinstance(game,str):
            g = self.get_game(game)
        elif isinstance(game,games.Game):
            g = self.get_game(game.game_id)
        else:
            raise TypeError('game')
        
        if not g:
            raise LookupError('game')
            
        backups=[]
        sql='SELECT id,filename,checksum,hash,ftp_transferred FROM filelist WHERE game=?;'
        sql2='SELECT id,filename,use_ftp,ftp_transferred FROM filelist_extrafiles WHERE file=?;'
        cur = self._db.cursor()
        cur.execute(sql,(game.id,))
        
        for row in cur:
            extrafiles = []
            cur2 = self._db.cursor()
            cur2.execute(sql2,(row[0],))
            for row2 in cur2:
                extra = {
                    'id':int(row2[0]),
                    'filename':row2[1],
                    'use_ftp':self._db_to_bool(row2[2]),
                    'transferred': self._db_to_bool(row2[3])
                }
                extrafiles.append(extra)
                
            fdesc = {
                'game': g,
                'id':int(row[0]),
                'filename': row[1],
                'checksum': row[2],
                'hash': row[3],
                'ftp_transferred': self._db_to_bool(row[4]),
                'extrafiles': extrafiles}
            backups.append(fdesc)
            
        return backups
    # get_game_backups()
        
    def get_game_backup(self,game,filename):
        backup = {}
        
        if isinstance(game,str):
            g = self.get_game(game)
        elif isinstance(game,games.Game):
            g = self.get_game(game.game_id)
        else:
            raise TypeError('game')
            
        if not g:
            raise ValueError('game')
            
        sql = "SELECT id,filename,checksum,hash,ftp_transferred FROM filelist WHERE game=? AND filename=?;"
        sql2 = "SELECT id,filename,use_ftp,ftp_transferred FROM filelist_extrafiles WHERE file=?;"
        
        cur = self._db.cursor()
        cur.execute(sql,(game.id,os.path.basename(filename)))
        
        row = cur.fetchone()
        if row:
            extrafiles = []
            cur2 = self._db.cursor()
            cur2.execute(sql2,(row[0],))
            for row2 in cur2:
                extra = {
                    'id': int(row2[0]),
                    'filename': row2[1],
                    'use_ftp': self._db_to_bool(row2[2]),
                    'ftp_transferred': self._db_to_bool(row2[3])
                }
                extrafiles.append(extra)
                
            backup = {
                'game':g,
                'id': int(row[0]),
                'filename':row[1],
                'checksum':row[2],
                'hash':row[3],
                'ftp_transferred': self._db_to_bool(row[4]),
                'extrafiles': extrafiles
            }
            
        return backup
    # get_game_backup()
    
    def delete_game_backup(self,game,filename):
        backup = self.get_game_backup(game,filename)
        
        if backup:
            sql1 = "DELETE FROM filelist_extrafiles WHERE file=?;"
            sql2 = "DELETE FROM filelist WHERE id=?;"
            cur = self._db.cursor()
            cur.execute(sql1,(backup['id'],))
            cur.execute(sql2,(backup['id'],))
            self._db.commit()
    # delete_game_backup()
    
    def set_game_backup_ftp_transferred(self,game,filename,transferred=True):
        backup = self.get_game_backup(game,filename)
        
        if backup:
            sql = "UPDATE filelist SET ftp_transferred=? WHERE id=?;"
            cur = self._db.cursor()
            cur.execute(sql,(self._bool_to_db(transferred),backup['id']))
            self._db.commit()
    # set_game_backup_ftp_transferred()
    
    def set_game_backup_extrafile_ftp_transferred(self,game,filename,extrafile,transferred=True):
        backup = self.get_game_backup(game,filename)
        backup_extrafile = {}
        if backup:
            for i in backup['extrafiles']:
                if i['filename'] == extrafile:
                    backup_extrafile = i
                    break
        if extrafile:
            sql = 'UPDATE filelist_extrafiles SET ftp_transferred=? WHERE id=?;'
            cur = self._db.cursor()
            cur.execute(sql,(self._bool_to_db(transferred),backup_extrafile['id']))
            self._db.commit()
    # set_game_backup_extrafile_ftp_transferred()
    
    def add_ignore_steamapp(self,appid):
        if not self.ignore_steamapp(appid):
            sql = 'INSERT INTO steamapp_ignore (steam_appid) VALUES (?);'
            cur = self._db.cursor()
            cur.execute(sql,(appid,))
            self._db.commit()
            
    def remove_ignore_steamapp(self,appid):
        sql = 'DELETE FROM steamapp_ignore WHERE steam_appid=?;'
        cur = self._db.cursor()
        cur.execute(sql,(appid,))
        self,_db.commit()
        
    def ignore_steamapp(self,appid):
        sql = 'SELECT id FROM steamapp_ignore WHERE steam_appid=?;'
        cur = self._db.cursor()
        cur.execute(sql,(appid,))
        
        row = cur.fetchone()
        if row and row[0] > 0:
            return True
        return False
        
    def get_pysgbackup_plugin(self,plugin_name):
        sql = 'SELECT id,name,version,enabled,sgbackup_plugin,sgbackup_plugin_enable FROM pysgbackup_plugins WHERE name=?;'
        cur = self._db.cursor()
        cur.execute(sql,(plugin_name,))
        row = cur.fetchone()
        if row:
            sgbackup_plugin = None
            if row[4]:
                sql2 = "SELECT name,version,enabled FROM plugins WHERE id=?;"
                cur2 = self._db.cursor()
                cur2.execute(sql2,(int(row[4]),))
                
                row2 = cur2.fetchone()
                if row2:
                    sgbackup_plugin = {
                        'id': int(row[4]),
                        'name': row2[0],
                        'version': row2[1],
                        'enabled': self._db_to_bool(row2[2])
                    }
            plugin = {
                'id': row[0],
                'name': row[1],
                'version': row[2],
                'enabled': self._db_to_bool(row[3]),
                'sgbackup_plugin': sgbackup_plugin,
                'sgbackup_plugin_enable': self._db_to_bool(row[5])
            }
            return plugin
        return None
    # get_pysgbackup_plugin()
    
    def has_pysgbackup_plugin(self,plugin_name):
        sql = "SELECT id FROM pysgbackup_plugins WHERE name=?;"
        cur = self._db.cursor()
        cur.execute(sql,(plugin_name,))
        row = cur.fetchone()
        if row and int(row[0]):
            return True
        return False
    # has_pysgbackup_plugin()
    
    def get_pysgbackup_plugin_enabled(self,plugin_name):
        plugin = self.get_pysgbackup_plugin(plugin_name)
        if not plugin:
            return False
        
        if plugin['enabled']:
            return True
            
        if plugin['sgbackup_plugin_enable'] and plugin['sgbackup_plugin'] and plugin['sgbackup_plugin']['enabled']:
            return True
            
        return False
    # get_pysgbackup_plugin_enabled()
    
    def add_pysgbackup_plugin(self,plugin):
        if self.has_pysgbackup_plugin(plugin.name):
            db_plugin = self.get_pysgbackup_plugin(plugin.name)
            sql = "UPDATE pysgbackup_plugins SET name=?,version=?,enabled=?,sgbackup_plugin=?,sgbackup_plugin_enable=? WHERE id=?;"
            sgbackup_plugin_id = None
            enable = False
            if plugin.sgbackup_plugin:
                sgbackup_plugin_enable = plugin.sgbackup_plugin_enable
            else:
                sgbackup_plugin_enable = False
                
            if not plugin.sgbackup_plugin and not plugin.sgbackup_plugin_enable:
                enable = plugin.enabled
            if plugin.sgbackup_plugin:
                db_sgbackup_plugin = self.get_plugin(plugin.sgbackup_plugin.name)
                if db_sgbackup_plugin:
                    sgbackup_plugin_id = db_sgbackup_plugin['id']
                    
            sql_args = (
                plugin.name,
                plugin.version,
                self._bool_to_db(enable),
                sgbackup_plugin_id,
                self._bool_to_db(sgbackup_plugin_enable),
                db_plugin['id']
            )
        else:
            sql = "INSERT INTO pysgbackup_plugins (name,version,enabled,sgbackup_plugin,sgbackup_plugin_enable) VALUES (?,?,?,?,?);"
            sgbackup_plugin_id = None
            enabled = False
            if plugin.sgbackup_plugin:
                db_sgbackup_plugin = self.get_plugin(plugin.sgbackup_plugin.name)
                if db_sgbackup_plugin:
                    sgbackup_plugin_id = db_sgbackup_plugin['id']
            if not plugin.sgbackup_plugin and not plugin.sgbackup_plugin_enable:
                enabled = plugin.enabled
                
            sql_args = (
                plugin.name,
                plugin.version,self._bool_to_db(enabled),
                sgbackup_plugin_id,
                self._bool_to_db(plugin.sgbackup_plugin_enable)
            )
            
        cur = self._db.cursor()
        cur.execute(sql,sql_args)
        self._db.commit()
    # add_pysgbackup_plugin()
    
    def enable_pysgbackup_plugin(self,plugin_name):
        plugin = self.get_pysgbackup_plugin(plugin_name)
        if plugin:
            if plugin['sgbackup_plugin'] and plugin['sgbackup_plugin_enable']:
                self.enable_plugin(plugin['sgbackup_plugin']['name'])
            else:
                sql = "UDPATE pysgbackup_plugins SET enabled='Y' WHERE id=?;"
                cur = self._db.cursor()
                cur.execute(sql,(plugin['id'],))
                self._db.commit()
    # enable_pysgbackup_plugin()
    
    def disable_pysgbackup_plugin(self,plugin_name):
        plugin = self.get_pysgbackup_plugin(plugin_name)
        if plugin:
            sql = "UPDATE pysgbackup_plugins SET enabled='N' WHERE id=?;"
            cur = self._db.cursor()
            cur.execute(sql,(plugin['id'],))
            self._db.commit()
            
            if plugin['sgbackup_plugin'] and plugin['sgbackup_plugin_enable']:
                self.disable_plugin(plugin['sgbackup_plugin']['name'])
    # disable_pysgbackup_plugin()
# Database class

def update(db,force=False):
    def _gameconf_changed(db,gameconf_list_db,gameconf_list_conf):
        def gameconf_in_db(db,gameconf):
            gc = db.get_gameconf_by_filename(gameconf.filename)
            if (gc):
                return True
            return False
        # gameconf_in_db()
        
        def gameconf_in_list_changed(gameconf,gameconf_list):
            for i in gameconf_list:
                if (gameconf.filename == i.filename) and (gameconf.checksum == i.checksum):
                        return False                    
            return True
        # gameconf_in_list_changed
        
        for i in gameconf_list_conf:
            if not gameconf_in_db(db,i):
                return True
                
        for i in gameconf_list_db:
            if gameconf_in_list_changed(i,gameconf_list_conf):
                return True
        return False
    # _gameconf_changed()
    
    def _gameconf_removed(filename):
        if not os.path.isfile(filename):
            return True
        return False
    # _gameconf_removed()
    
    def _plugin_changed(db,plugin):
        spec = db.get_plugin(plugin.name)
        
        pv = plugin.version.split('.')
        dbv = spec['version'].split('.')
        
        if (len(pv) >= 3 and len(dbv) >= 3):
            if (pv[0] == dbv[0] and pv[1] <= dbv[1] and pv[2] <= pv[2]):
                return False
            return True
        elif (len(pv) >= 2 and len(dbv) >= 2):
            if (pv[0] == dbv[0] and pv[1] <= dbv[1]):
                return False
            return True
        else:
            return (pv[0] != dbv[0])
    # _plugin_changed()
    
    def _plugin_deleted(spec):
        if spec['name'] in plugins.PLUGINS:
            return False
        return True
                
    for gid in games.get_games():
        print('GameID: {0}'.format(gid))
        game = games.parse_gameconf(gid)
        if not game:
            continue
            
        if config.CONFIG['verbose']:
            print("Processing: {0}".format(game.name))
            
        if force or not db.has_game(gid):
            has_game = True
            if not db.has_game(gid):
                has_game = False
                print("Adding game: {0}".format(game.name))
            else:
                print("Updating game: {0}".format(game.name))
                
            gcd_list = games.get_gameconf_data(gid)
            db.add_game(game,gcd_list)
            if (has_game):
                gcd_db = db.get_gameconf(gid)
                for gcd in gcd_db:
                    if _gameconf_removed(gcd.filename):
                        if config.CONFIG['verbose']:
                            print("Removing gameconf '{0}' from database".format(gcd.filename,gid))
                        db.delete_gameconf(gcd.filename)
            continue
            
        gcd_db = db.get_gameconf(gid)
        gcd_conf = games.get_gameconf_data(gid)
        
        if (_gameconf_changed(db,gcd_db,gcd_conf)):
            print("Updating game: {0}".format(gid))
            game = games.parse_gameconf(gid)
            db.add_game(game,gcd_conf)
            for gcd in gcd_db:
                if _gameconf_removed(gcd.filename):
                    if config.CONFIG['verbose']:
                        print("Removing gameconf '{0}' from database".format(gcd.filename,gid))
                    db.delete_gameconf(gcd.filename)
                  
                    
    # check for deleted plugins
    for spec in db.list_plugins():
        if _plugin_deleted(spec):
            if config.CONFIG['verbose']:
                pass
            db.delete_plugin(spec['name'])
        
    #check for plugins
    for name,plugin in plugins.PLUGINS.items():
        if db.has_plugin(plugin.name):
            if _plugin_changed(db,plugin):
                db.update_plugin(plugin)
        else:
            db.add_plugin(plugin)
# update()
