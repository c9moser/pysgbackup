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
from .. import config,database

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

_COMMAND_STEAMLIB_HELP = """sgbackup steamlib

USAGE:
======
  sgbackup steamlib show
  sgbackup steamlib <add|remove> [OPTIONS] <Path> ...
  
OPTIONS:
========
  -g | --global         Write to global config.
  -V | --no.verbose     Disable verbose messages.
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
        for sl in config.CONFIG['steam.libraries'].split(','):
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
        
    steam_libs = config.CONFIG['steam.libraries'].split(',')    
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
    
plugin = {
    'name': 'steam',
    'description': 'Steam library plugin',
    'commands': {
        'steamlib': {
            'description': 'Show|Add|Remove Steam Libraries.',
            'function': command_steamlib,
            'help': _COMMAND_STEAMLIB_HELP
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

