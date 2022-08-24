#-*- coding:utf-8 -*-

import os
from sgbackup import config
import configparser

import hashlib

from ._game import Game, GameConf

def get_conf_dirs():
    ret = [
        os.path.dirname(__file__),
        config.CONFIG['user-gameconf-dir']]
        
    return ret

def parse_gameconf(game_id):
    def _real_parse_file(f,game=None):
        parser = configparser.ConfigParser()
        parser.read(f)
        
        name=None
        sg_name=None
        sg_dir=None
        sg_root=None
        
        sect='variables'
        if parser.has_section(sect):
            for i in parser.options(sect):
                pass
        
        sect='game'
        if parser.has_section(sect):
            if parser.has_option(sect,'name'):
                name=parser.get(sect,'name')
            if parser.has_option(sect,'savegame-name'):
                sg_name=parser.get(sect,'savegame-name')
            if parser.has_option(sect,'savegame-root'):
                sg_root=parser.get(sect,'savegame-root')
            if parser.has_option(sect,'savegame-dir'):
                sg_dir=parser.get(sect,'savegame-dir')
            
        steam_appid = None
        sect = 'steam'
        if parser.has_section(sect):
            if parser.has_option(sect,'appid'):
                steam_appid = parser.get(sect,'appid')
        
        sect='game-variables'
        variables = {}
        if parser.has_section(sect):
            for var in parser.options(sect):
                variables[var] = parser.get(sect,var)
                
        if not game:
            if not name or not sg_name or not sg_dir or not sg_root:
                return None
            return Game(game_id,name,sg_name,sg_root,sg_dir,variables=variables,steam_appid=steam_appid)
        
        if game_id:
            game.game_id = game_id
        if name:
            game.name = name
        if sg_name:
            game.savegame_name = sg_name
        if sg_root:
            game.savegame_root = sg_root
        if steam_appid:
            game.steam_appid = steam_appid
        if variables:
            game.raw_variables.update(variables)
            
        return game
    # _real_parse_file()
    
    game=None
    for d in get_conf_dirs():
        conf = os.path.join(d,'.'.join((game_id,'game')))

        if os.path.isfile(conf):
            game=_real_parse_file(conf,game)
            
    return game
# parse_gameconf()


def get_gameconf_data(game_id):
    ret=[]
    
    for d in get_conf_dirs():
        f = os.path.join(d,'.'.join((game_id,'game')))
        if os.path.isfile(f):
            with open(f,'rb') as conf:
                checksum=hashlib.md5(conf.read()).hexdigest()
                if d == config.CONFIG['user-gameconf-dir']:
                    user_file=True
                else:
                    user_file=False
                ret.append(GameConf(f,checksum,user_file))                            
    return ret     
# get_gameconf_data            

def get_gameconf_data_by_filename(filename,game_id=""):
    ret = None
    
    if (os.path.isfile(filename)):
        if os.path.dirname(filename) == config.CONFIG["user-gameconf-dir"]:
            user_file=True
        else:
            user_file=False
            
        with open(filename,"rb") as conf:
            checksum = hashlib.md5(conf.read()).hexdigest()
            
        ret = GameConf(filename,checksum,user_file)
        
        if game_id:
           ret.game_id = game_id
            
    return ret
        

def get_games():
    """
    return a list of game_id's.
    """
    gameconf = []
    for d in get_conf_dirs():
        if (os.path.exists(d)):
            for f in os.listdir(d):
                if f.endswith('.game'):
                    gid = os.path.splitext(os.path.basename(f))[0]
                    if not gid in gameconf:
                        gameconf.append(gid)
    gameconf.sort()
    return gameconf
    

