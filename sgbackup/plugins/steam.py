#-*- coding:utf-8 -*-
################################################################################
# sgbackup.plugin.steam
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

import os
import sys
import getopt
import glob
import configparser
from .. import config,database,games

default_steam_lib = ""
__test_steam_libs= [
    os.path.expandvars((os.path.join('${SYSTEMDRIVE}','Program Files (X86)','Steam'))),
    os.path.expandvars((os.path.join('${SYSTEMDRIVE}','Program Files','Steam')))
]

for sl in __test_steam_libs:
    if os.path.isdir(sl):
        default_steam_lib = sl
        break
del __test_steam_libs

def get_steamlibs():
    if (('steam.libraries' not in config.CONFIG) 
            or not config.CONFIG['steam.libraries'].strip()):
        return []
        
    return config.CONFIG['steam.libraries'].split(',')
# get_steamlibs()
    
def scan_steamlibs():
    steam_games=[]
    
    for lib in get_steamlibs():
        appdir=os.path.join(lib,'steamapps')
          
        for manifest in glob.glob(os.path.join(appdir,'appmanifest_*.acf')):
            manifest_id = os.path.basename(manifest)
            manifest_id = manifest_id[len('appmanifest_'):-4]
            
            appid=""
            name=""
            installdir=""
            with open(manifest,'r') as ifile:
                for i in ifile.readlines():
                    i = i.strip()
                    if not i:
                        continue
                    if i.startswith('"appid"'):
                        key,value = i.split(None,1)
                        appid=value[1:-1]
                    elif i.startswith('"name"'):
                        key,value = i.split(None,1)
                        name=value[1:-1]
                    elif i.startswith('"installdir"'):
                        key,value = i.split(None,1)
                        installdir=os.path.join(appdir,'common',value[1:-1])
                    
            if int(manifest_id) == int(appid):
                g = {
                    'name': name,
                    'appid': appid,
                    'installdir': installdir
                }
                steam_games.append(g)
    return steam_games
# scan_steamlibs()

def get_game_from_gameconf(appid):
    directories = games.get_conf_dirs()
    gameconf_list = []
    for d in directories:
        for i in os.listdir(d):
            if i.startswith('.') or i.startswith('_'):
                continue
            gc = None
            if i.endswith('.game'):
                gc = i[:-5]
            elif i.endswith('.game.in'):
                gc = i[:-8]
            else:
                continue
            
            if gc and not gc in gameconf_list:
                gameconf_list.append(gc)
      
    for i in gameconf_list:
        gcfiles = []
        for d in directories:
            gcf_in = os.path.join(d,'.'.join((i,'game','in')))
            gcf = os.path.join(d,'.'.join((i,'game')))
            if not gcfiles and os.path.isfile(gcf_in):
                gcfiles.append(gcf_in)
            if os.path.isfile(gcf):
                gcfiles.append(gcf)
        parser = configparser.ConfigParser()
        
        for gcf in gcfiles:
            if gcf.endswith('.game.in'):
                game_id = os.path.basename(gcf[:-8])
            else:
                game_id = os.path.basename(os.path.splitext(gcf)[0])
            parser.read(gcf)
        g = games.parse_config(parser,game_id)
        if g.steam_appid == appid:
            return g
            
    return None
            
# get_game_from_gameconf

_COMMAND_STEAMLIB_HELP = """sgbackup steamlib

USAGE:
======
  sgbackup steamlib show
  sgbackup steamlib <add|remove> [OPTIONS] <Path> ...
  
OPTIONS:
========
  -g | --global         Write to global config.
  -V | --no-verbose     Disable verbose messages.
  -v | --verbose        Enable verbose messages.
"""
def command_steamlib(db,argv):
    if not argv:
        print('[sgbackup steamlib] ERROR: No command given!',file=sys.stderr)
        print(_COMMAND_STEAMLIB_HELP)
        sys.exit(2)
        
    if argv[0] not in ['add','remove','show']:
        print('[sgbackup steamlib] ERROR: Unknown command "{0}"!'.format(argv[0]),file=sys.stderr)
        print(_COMMAND_STEAMLIB_HELP)
        sys.exit(2)
        
    if argv[0] == 'show':
        for sl in get_steamlibs():
            print(sl)
        sys.exit(0)
    
    try:
        opts,args = getopt.getopt(argv[1:],'gVv',['global','no-verbose','verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        print(_COMMAND_STEAMLIB_HELP)
        sys.exit(2)
        
    global_config = False
    for o,a in opts:
        if o == '-g' or o == '--global':
            global_config = True
        elif o == '-V' or o == '--no-verbose':
            config.CONFIG['verbose'] = False
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
        
    steam_libs = get_steamlibs()    
    if argv[0] == 'add':
        if not args:
            print('[sgbackup steamlib add] ERROR: No Steam Library given!',file=sys.stderr)
            print(_COMMAND_STEAMLIB_HELP)
            sys.exit(2)
            
        for sl in args:
            if not os.path.isdir(sl):
                print('Steam Library "{0}" does not exist!'.format(sl))
                sys.exit(3)
        
        
        for sl in args:
            if sl not in steam_libs:
                if config.CONFIG['verbose']:
                    print("<adding steam library> {0}".format(sl))
                steam_libs.append(sl)
            elif config.CONFIG['verbose']:
                print('Steamlib "{0}" already exists! SKIPPING!'.format(sl))
    elif argv[0] == 'remove':
        if not args:
            print('[sgbackup steamlib remove] ERROR: No Steam Library given!',file=sys.stderr)
            print(_COMMAND_STEAMLIB_HELP)
            sys.exit(2)
            
        for sl in args:
            if sl in steam_libs:
                if config.CONFIG['verbose']:
                    print("<removing steam library> {0}".format(sl))
                for i in range(len(steam_libs)):
                    if steam_libs[i] == sl:
                        del steam_libs[i]
                        break;
            elif config.CONFIG['verbose']:
                print('Steam Library "{}" not in list! SKIPPING!'.format(sl))
                
    config.set_config('steam.libraries',','.join(steam_libs))
    if global_config:
        cfile = config.CONFIG['global-config']
    else:
        cfile = config.CONFIG['user-config']
        
    config.write_config(cfile,global_config)
# command_steamlib    
    
_COMMAND_STEAM_HELP='''sgbackup steam

USAGE:
======
  sgbackup steam [OPTIONS] COMMAND [ARG ...]
  
OPTIONS:
========
  -V | --no-verbose     Disable verbose output.
  -v | --verbose        Enable verbose output.
  
COMMANDS:
=========
  list                  List all steam games found.
  scan                  Scan Steamlibraries for games not in database.
'''

def command_steam(db,argv):
    try:
        opts,args = getopt.getopt(argv,'vV',['no-verbose','verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        print(_COMMAND_STEAM_HELP)
        sys.exit(2)
        
    if not args:
        print('[sgbackup steam] No command given!',file=sys.stderr)
        print(_COMMAND_STEAM_HELP)
        sys.exit(2)

    commands=[
        'list',
        'scan'
    ]
    cmd = args[0]
    if cmd not in commands:
        print('[sgbackup steam] Unknown command "{0}"!'.format(cmd),file=sys.stderr)
        print(_COMMAND_STEAM_HELP)
        sys.exit(2)
    
    for o,a in opts:
        if o == '-V' or o == '--no-verbose':
            config.CONFIG['verbose'] = False
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
    
    if cmd == 'list':
        steam_games = scan_steamlibs()
        gid_len=0
        appid_len=0
        for i in steam_games:
            if len(i['appid']) > appid_len:
                appid_len = len(i['appid'])
                
            g = db.get_game_by_steam_appid(i['appid'])
            i['game'] = g
            if g:
                if len(g.game_id) > gid_len:
                    gid_len = len(g.game_id)
        
        for i in steam_games:
            if i['game']:
                gid = i['game'].game_id + (' ' * (gid_len - len(i['game'].game_id)))
            else:
                gid = ' ' * gid_len
                
            appid = i['appid'] + (' ' * (appid_len - len(i['appid'])))
            
            print('{0} {1} {2}'.format(appid,gid,i['name']))
        return
    elif cmd == 'scan':
        steam_games = scan_steamlibs()
        for i in steam_games:
            g = db.get_game_by_steam_appid(i['appid'])
    
            if not g and not db.ignore_steamapp(i['appid']):
                input_valid = False
                add_game = False
                while not input_valid:
                    x = input('Game "{0}" not found. Do you want to add it? [y/n/i]: '.format(i['name']))
                    if x.lower() == 'y' or x.lower() == 'yes':
                        add_game = True
                        input_valid = True
                    elif x.lower() == 'n' or x.lower() == 'no':
                        add_game = False
                        input_valid = True
                    elif x.lower() == 'i' or x.lower() == 'ignore':
                        add_game = False
                        input_valid = True
                        db.add_ignore_steamapp(i['appid'])
                    else:
                        input_valid = False
                
                if add_game:      
                    game = get_game_from_gameconf(i['appid'])
                    if not game:
                        game = games.Game('game',i['name'],'','','',
                                          id=0,
                                          steam_appid=i['appid'],
                                          variables={'INSTALLDIR':i['installdir']})
                    else:
                        game.variables.update({'INSTALLDIR':i['installdir']})
                        
                    games.add_game(db,game=game,ask=True)
        return  
# command_steam()

plugin = {
    'name': 'steam',
    'description': 'Steam library plugin',
    'commands': {
        'steamlib': {
            'description': 'Show|Add|Remove Steam Libraries.',
            'function': command_steamlib,
            'help': _COMMAND_STEAMLIB_HELP
        },
        'steam': {
            'description': 'Perform actions on steam games.',
            'function': command_steam,
            'help': _COMMAND_STEAM_HELP
        }
    },
    'config': {
        'global': True,
        'local': True,
        'section': 'steam',
        'values': {
            'steam.libraries': {
                'option': 'libraries',
                'type': 'string',
                'default': default_steam_lib
            }
        }
    }
}

