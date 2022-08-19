#!/usr/bin/env python
#-*- coding:utf-8 -*-

################################################################################
# sgrestore.py
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

import sys
import os
import shelve
import getopt
import hashlib

try:
    import sgbackup
except ImportError as error:
    print('ERROR: Unable to import sgbackup! ({0})'.format(error),file=sys.stderr)
    sys.exit(3)

HELP = """sgrestore

USAGE:
======
  sgrestore <-h|--help|-l|--list>
  sgrestore [-v] <-a>
  sgrestore [-v] GameID ...
  
OPTIONS:
========
  -a | --all        Select all games to restore.
  -h | --help       Print this help message.
  -l | --list       List all games.
  -v | --verbose    Print verbose messages.
"""

CONFIG={
    'iso-root-directory': os.path.join(os.path.dirname(__file__)),
    'backup-directory': os.path.join(os.path.dirname(__file__),'SaveGames'),
    'game-shelve': os.path.join(os.path.dirname(__file__),'SaveGames','games')
}


def get_game_list():
    gl  = []
    
    with shelve.open(CONFIG['game-shelve']) as d:
        for game_id in sorted(d.keys()):
            game_spec = d['game_id']
            gl.append(game_spec)
            
    return gl


def main():
    try:
        opts,args = getopt.getopt(sys.argv[1:],'ahlv',['all','help','list','verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        print(HELP)
        sys.exit(2)

    verbose = False
         
    for o,a in opts:
        if o == '-h' or o == '--help':
            print(HELP)
            sys.exit(0)
        elif o == '-l' or o == '--list':
            gl = get_game_list()
            width=0
            for g in gl:
                if len(g['game-id']) > width:
                    width = len(g['game-id'])
            width += 1
            
            for g in gl:
                print(g['game-id'] + ' ' * (width - len(g['game-id'])) + g['name'])
            sys.exit(0)
        elif o == '-a' or o == '--all':
            with open(CONFIG['game-shelve']) as d:
                for gameid in d.keys():
                    found=False
                    for i in args:
                        if gameid == i:
                            found=True
                            break
                    if not found:
                        args.append(gameid)
        elif o == '-v' or o == '--verbose':
            verbose = True
            sgbackup.config.CONFIG['verbose'] = True
            
    if not args:
        print(HELP)
        sys.exit(2)
        
    with shelve.open(CONFIG['game-shelve']) as d:
        for gameid in args:
            if not gameid in d.keys():
                print ('GameID "{}" not found!'.format(gameid))
                print ('Use "sgrestore --list" to show valid GameIDs.')
                sys.exit(2)
                
        for gameid in args:
            g = d[gameid]
            backup = None
            if verbose:
                print('Processing game "{}"'.format(g['name']))
            if len(g['files']) == 1:
                backup = g['files'][0]
            elif len(g['files']) > 1:
                count = 1
                choose={}
                print("More than one SaveGameBackup found.")
                for i in g['files'].keys():
                    print('{0}\t{1}'.format(count,os.path.basename(i)))
                    choose[count] = i
                valid_input = False
                ignore = False
                while not valid_input:
                    x = input('Please choose the file you want to reatore or press "q" to quit: ')
                    if x.lower() == 'q':
                        valid_input = True
                        ignore = True
                    else:
                        try:
                            x = int(x)
                            if x in choose:
                                valid_input=True
                                ignore = False
                                backup = choose[x]
                        except:
                            continue
            if backup:
                print('[check] {} ... '.format(backup))
                h = hashlib.new(g['files'][backup]['checksum'])
                backup_file = os.path.join(CONFIG['backup-directory'],g['savegame-name'],backup)
                with open(backup_file,'rb') as ifile:
                    h.update(ifile.read())
                check_hash = h.hexdigest()
                if g['files'][backup]['hash'] == check_hash:
                    print('OK')
                else:
                    print('FAILED')
                    print('Skipping file "{0}"!'.format(backup))
                    continue
                
                archiver = sgbackup.backup.get_archiver_for_file(backup_file)
                if not archiver:
                    print('ERROR: No archiver for file "{}" found! SKIPPING!'.format(backup), file=sys.stderr)
                    continue
                    
                print("[restore] {}".format(backup))
                archiver.restore(backup_file,g['savegame-root'])                
# main()
                
    
if __name__ == '__main__':
    main()

