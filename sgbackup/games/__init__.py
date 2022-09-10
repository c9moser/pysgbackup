#-*- coding:utf-8 -*-

import os
from sgbackup import config
import configparser

import hashlib

from ._game import Game, GameConf
from .. import database

def get_conf_dirs():
    ret = [
        os.path.dirname(__file__),
        config.CONFIG['user-gameconf-dir']
    ]
        
    return ret
# get_conf_dirs()

def parse_config(parser,game_id=''):
    cfg = {
        'id': 0,
        'game_id': 'game',
        'name': '',
        'savegame_name': '',
        'savegame_dir': '',
        'savegame_root': '',
        'steam_appid': None,
        'variables': {}
    }
    if game_id:
        cfg['game_id'] = game_id
    
    sect = 'game'
    if parser.has_section(sect):
        if parser.has_option(sect,'game-id'):
            cfg['game_id'] = parser.get(sect,'game-id')
        if parser.has_option(sect,'name'):
            cfg['name'] = parser.get(sect,'name')
        if parser.has_option(sect,'savegame-name'):
            cfg['savegame_name'] = parser.get(sect,'savegame-name')
        if parser.has_option(sect,'savegame-root'):
            cfg['savegame_root'] = parser.get(sect,'savegame-root')
        if parser.has_option(sect,'savegame-dir'):
            cfg['savegame_dir'] = parser.get(sect,'savegame-dir')
         
    sect = 'steam'
    if parser.has_section(sect):
        if parser.has_option(sect,'appid'):
            cfg['steam_appid'] = parser.get(sect,'appid')
            
    sect = 'variables'
    if parser.has_section(sect):
        for var in parser.options(sect):
            cfg['variables'][var] = parser.get(sect,var)
            
    return Game(
        cfg['game_id'],
        cfg['name'],
        cfg['savegame_name'],
        cfg['savegame_root'],
        cfg['savegame_dir'],
        steam_appid = cfg['steam_appid'],
        variables = cfg['variables'])
# parse_config()

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
        f = os.path.normpath(os.path.join(d,'.'.join((game_id,'game'))))
        if os.path.isfile(f):
            with open(f,'rb') as conf:
                checksum=hashlib.md5(conf.read()).hexdigest()
                if d == config.CONFIG['user-gameconf-dir']:
                    user_file=True
                else:
                    user_file=False
                
                gc = GameConf(f,checksum,user_file)
                gc.game_id = game_id
                ret.append(gc)
    return ret     
# get_gameconf_data            

def get_gameconf_data_by_filename(filename,game_id=""):
    ret = None
    
    fn = os.path.normpath(filename)
    if (os.path.isfile(fn)):
        if os.path.normpath(os.path.dirname(filename)) == os.path.normpath(config.CONFIG["user-gameconf-dir"]):
            user_file=True
        else:
            user_file=False
            
        with open(fn,"rb") as conf:
            checksum = hashlib.md5(conf.read()).hexdigest()
            
        ret = GameConf(fn,checksum,user_file)
        
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
    
def add_game(db,game=None,ask=True):
    if ask:
        if not game:
            game = Game('game','','','','')
           
        game_ok = False 
        settings=[
            {'name':'Name','attr':'name','raw':False},
            {'name':'GameID','attr':'game_id','raw':False},
            {'name':'SaveGame Name','attr':'savegame_name','raw':False},
            {'name':'SaveGame Root','attr':'savegame_root','raw':True},
            {'name':'SaveGame Dir','attr':'savegame_dir','raw':True},
            {'name':'Steam Appid','attr':'steam_appid','raw':False}
        ]
        while not game_ok:
            for i in settings:
                print('{0}: [{1}]'.format(i['name'],getattr(game,i['attr'])))
                if i['raw']:
                    print('{0} RAW: [{1}]'.format(i['name'],getattr(game,'_'.join(('raw',i['attr'])))))
                value = input('>> ')
                if value:
                    setattr(game,i['attr'],value)
        
            run_again = False
            add_var = False
            while not run_again:
                value = input('Add a variable? [Y/n]: ')
                if value.lower() == 'n' or value.lower() == 'no':
                    run_again = True
                    add_var = False
                    break
                elif value.lower() == 'y' or value.lower() == 'yes':
                    run_again = False
                    add_var = True
                else:
                    run_again = False
                    add_var = False
                    continue
                
                if add_var:
                    var_name = input('Variable Name: ')
                    var_value = input('Variable Value: ')
                    game.raw_variables[var_name] = var_value
                
            for i in settings:
                print('{0}: {1}'.format(i['name'],getattr(game,i['attr'])))
                if i['raw']:
                    print('{0} RAW: {1}'.format(i['name'],getattr(game,'_'.join(('raw',(i['attr']))))))
            print('VARIABLES:')
            for k,v in game.raw_variables.items():
                print('  {0}={1}'.format(k,v))
            input_ok = False
            while not input_ok:
                value = input("Are the game-settings OK? [yes/no] ")
                if value.lower() == 'y' or value.lower() == 'yes':
                    input_ok = True
                    game_ok = True
                    break
                elif value.lower() == 'n' or value.lower() == 'no':
                    input_ok = True
                    game_ok = False
                    break
                else:
                    input_ok = False
                    
    if not game:
        raise ValueError('Value "game" not set!')
        
    parser=configparser.ConfigParser()
    sect = 'game'
    parser.add_section(sect)
    parser.set(sect,'name',game.name)
    parser.set(sect,'savegame-name',game.savegame_name)
    parser.set(sect,'savegame-root',game.raw_savegame_root)
    parser.set(sect,'savegame-dir',game.raw_savegame_dir)
    
    if game.steam_appid:
        parser.add_section('steam')
        parser.set('steam','appid',game.steam_appid)
    
    if game.raw_variables:
        sect='game-variables'
        parser.add_section(sect)
        for k,v in game.raw_variables.items():
            parser.set(sect,k,v)
    gcf = os.path.normpath(os.path.join(config.CONFIG['user-gameconf-dir'],'.'.join((game.game_id,'game'))))
    with open(gcf,'w') as ofile:
        parser.write(ofile)
                
    db.add_game(game,gameconf=[GameConf(gcf,user_file=True)])
# add_game()

def remove_game(db,game,force=False):
    if isinstance(game,Game):
        game_id = game.game_id
    elif isinstance(game,str):
        game_id = game
        
    db.delete_game(game_id)
    
    if not force:
        for d in get_conf_dirs():
            gcf = os.path.join(d,'.'.join((game_id,'game')))
            if os.path.isfile(gcf):
                delete_file = False
                if not force:
                    valid_input = False
                    while not valid_input:
                        x = input('Delete GameConf "{}"? [Y/n] '.format(gcf))
                        if x.lower() == 'y' or x.lower() == 'yes':
                            delete_file = True
                            valid_input = True
                            break
                        elif x.lower() == 'n' or x.lower() == 'no':
                            delete_file = False
                            valid_input = True
                            break
                        else:
                            valid_input = False
                            
                if force or delete_file:
                    try:
                        os.unlink(gcf)
                    except Exception as error:
                        print('Unable to delete file "{0}"! ({1})'.format(gcf,error))
# remove_game()

