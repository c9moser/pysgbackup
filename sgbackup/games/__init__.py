import os
from sgbackup import config
import configparser

import hashlib

from _game import Game, GameConf

def get_conf_dirs():
    ret = [
        os.path.dirname(__FILE__),
        config.CONFIG['sg-user-gameconf-dir']]
        
    return ret

def parse_game_conf(game_id):
    def _real_parse_file(f,game=None):
        parser = configparser.ConfigParser()
        parser.read(f)
        
        game_id=os.path.splitext(os.path.basename(f))
        name=None
        sg_name=None
        sg_dir=None
        sg_root=None
        
        sect='game'
        if parser.has_section(sect):
            if parser.has_option(sect,'name'):
                name=parser.get_option(sect,'name')
            if parser.has_option(sect,'savegame-name'):
                sg_name=parser.get_option(sect,'savegame-name')
            if parser.has_option(sect,'savegame-root'):
                sg_root=parser.get_option(sect,'savegame-root')
            if parser.has_option(sect,'savegame-dir')
                sg_dir=parser.get_option(sect,'savegame-dir')
        
        if not game:
            ret=Game(game_id,name,sg_name,sg_root,sg_dir)
            return ret
            
        if game_id:
            game.game_id = game_id
        if name:
            game.name = name
        if sg_name:
            game.savegame_name = sg_name
        if sg_root:
            game.savegame_root = sg_root
        if sg_dir:
            game.savegame_dir = sg_dir
            
        return game
    # _real_parse_file()
    
    for d in get_conf_dirs():
        conf = os.path.join(d,'.'.join(game_id,conf))
        game=None
        if os.path.isfile(conf):
            game=_real_parse_file(f,game)
            
    return game
# parse_game_conf()


def get_gameconf_data(game_id):
    ret=[]
    
    for d in get_conf_dirs():
        f = os.path.join(d,'.'.join(game_id,'.conf'))
        if os.path.isfile(f):
            with open(f,'br') as conf:
                checksum=hashlib.md5(conf.read()).hexdigest()
                if d == config.CONFIG['sg-user-gameconf-dir']:
                    user_file=True
                else:
                    user_file=False
                ret.append(GameConf(filename,checksum,user_file))                            
    return ret        
# get_gameconf_data            

def get_gameconfigs():
    """
    return a list of game_id's.
    """
    
    gameconf = []
    
    for d in get_conf_dirs():
        if (os.path.exists(d)):
            for f in os.listdir(d):
                if f.endswith('.conf'):
                    gid = os.path.splietext(os.path.basename(f))[0]
                    if not gid in gameconf:
                        gameconf.append(gid)
    gameconf.sort()
    return gameconf
    

