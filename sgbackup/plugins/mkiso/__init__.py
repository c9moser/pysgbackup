#-*- coding:utf-8 -*-
################################################################################
# sgbackup mkiso
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

try:
    import pycdlib
    plugin_available=True
except ImportError as error:
    plugin_available=False

if plugin_available:
    import getopt
    import sgbackup
    import os
    import sys
    import glob
    import datetime
    from sgbackup.config import CONFIG
    from sgbackup import help
    import shelve
    import hashlib
    import gi; from gi.repository import GLib
    
    COMMAND_MKISO_HELP="""sgbackup mkiso

USAGE
=====
  sgbackup mkiso [OPTIONS]
  
OPTIONS
=======
  -a | --all-finals     Store all finals in ISO file.
  -A | --no-all-finals  Don't put all finals in ISO file.
  -o | --output=FILE    Output to file FILE.
  -V | --no-verbose     Disable verbose messages.
  -v | --verbose        Enable verbose messages.
  
DESCRIPTION
===========
  Creates an ISO file from SaveGame-backups. 
  
  If --all-finals option is given, all finalized backups are included into the
  ISO-image. If --no-all-finals option is given, only the latest 
  SaveGame-backups are included into the ISO-image.
  
  If --output option is given, the ISO-file written will be filename and the
  maxiso check is not performed.
"""
    def command_mkiso(db,argv):
        try:
            opts,args = getopt.getopt(argv,'Aao:Vv', [
                                        'all-finals',
                                        'no-all-finals',
                                        'no-verbose',
                                        'output='
                                        'verbose'
                                      ])
        except getopt.GetoptError as error:
            print(error,file=sys.stderr)
            help.print_help('mkiso')
            sys.exit(2)
            
        if args:
            print("[sgbackup mkiso] This command does not take any arguments!",file=sys.stderr)
            help.print_help('mkiso')
            sys.exit(2)
            
        all_finals = CONFIG['mkiso.all-finals']
        check_maxiso = True
        dt = datetime.datetime.now()
        image_name = os.path.join(CONFIG['mkiso.directory'],
                                  "SaveGames.{}.iso".format(dt.strftime('%Y%m%d-%H%M%S')))
        for o,a in opts:
            if o == '-a' or o == '--all-finals':
                all_finals = True
            elif o == '-A' or o == '--no-all-finals':
                all_finals = False
            elif o == '-o' or o == '--output':
                check_maxiso = False
                if os.path.isabs(a):
                    image_name = a
                else:
                    image_name = os.path.join(os.getcwd(),a)
                    
                if not os.path.isdir(os.path.dirname(image_name)):
                    os.makedirs(os.path.dirname(image_name))
                    
                if os.path.isfile(image_name):
                    os.unlink(image_name)
                    
            elif o == '-V' or o == '--no-verbose':
                CONFIG['verbose'] = False
            elif o == '-v' or o == '--verbose':
                CONFIG['verbose'] = True
            
        iso_dirs=['/SaveGames']
        iso_files=[
            (os.path.join(os.path.dirname(__file__),'sgrestore.py'),'/sgrestore.py'),
            (os.path.join(os.path.dirname(__file__),'sgrestore.sh'),'/sgrestore'),
            (os.path.join(os.path.dirname(__file__),'sgrestore.bat'), '/sgrestore.bat')
        ]
        
        
        
        #FIX msys bug with burn software
        if sys.platform == 'win32':
            print(image_name.replace('/','\\'))
        else:
            print(image_name)

        game_list=[]
        for gid in db.list_game_ids():
            game = db.get_game(gid)
            game_dir = os.path.join(CONFIG['backup.dir'],game.savegame_name)
            files=[]
            if all_finals:
                files+=sgbackup.backup.find_all_final_backups(game)
                
            f = sgbackup.backup.find_latest_backup(game)
            if f: 
                if f not in files:
                    files.append(f)                
            if files:
                game_list.append((gid,game,files))
                iso_dirs.append('/'.join(('/SaveGames',game.savegame_name)))
                for i in files:
                    iso_files.append((i,'/'.join(('/SaveGames',game.savegame_name,os.path.basename(i)))))
                
        shelve_file=os.path.join(GLib.get_tmp_dir(),
                                 'sgbackup-mkiso.{}.{}'.format(GLib.get_user_name(),dt.strftime('%Y%m%d%H%M%S')),
                                 'games')
                                 
        if CONFIG['verbose']:
            print("creating game database ... ",end="")
        if not os.path.isdir(os.path.dirname(shelve_file)):
            os.makedirs(os.path.dirname(shelve_file))
            
        with shelve.open(shelve_file) as d:
            for game_id,game,files in game_list:
                game_spec_files = {}
                for f in files:
                    key = os.path.basename(f)
                    backup = db.get_game_backup(game,f)
                    if backup:
                        cksum = backup['checksum']
                        digest = backup['hash']
                    else:
                        cksum = CONFIG['backup.checksum']
                        h = hashlib.new(cksum)
                        with open(f,'rb') as ifile:
                            h.update(ifile.read())
                        digest = h.hexdigest()
                    game_spec_files[key] = {'checksum':cksum,'hash':digest}
                    
                
                game_spec={
                    'game-id': game.game_id,
                    'name': game.name,
                    'savegame-root': game.savegame_root,
                    'savegame-dir': game.savegame_dir,
                    'savegame-name': game.savegame_name,
                    'files': game_spec_files
                }
                d[game_id]=game_spec
        if CONFIG['verbose']:
            print('Done')
    
        for f in os.listdir(os.path.dirname(shelve_file)):
            if f == '.' or f == '..':
                continue
            iso_files.append((os.path.join(os.path.dirname(shelve_file),f),'/'.join(('/SaveGames',f))))
    
        if CONFIG['verbose']:
            print('creating ISO-file ... ',end='')
        disc = pycdlib.PyCdlib()
        disc.new(udf='2.60')
        for i in iso_dirs:
            disc.add_directory(udf_path=i)
            
        for filename,iso_name in iso_files:
            disc.add_file(filename,udf_path=iso_name)
            
        disc.write(image_name)
        if CONFIG['verbose']:
            print('DONE')
        
        # checking for max .iso files        
        if check_maxiso and CONFIG['mkiso.maxiso'] > 0:
            if CONFIG['verbose']:
                print('Check for max iso-files')
            n = CONFIG['mkiso.maxiso']
            count = 0
            for img in sorted(glob.glob(os.path.join(CONFIG['mkiso.directory'],'SaveGames.*.iso')),reverse=True):
                count += 1
                if count > n:
                    if CONFIG['verbose']:
                        print('Deleting "{}"'.format(img))
                    os.unlink(img)            
    # command_mkiso
    
    plugin={
        'name': 'mkiso',
        'description': 'Create ISO files with latest backups.',
        'commands': {
            'mkiso': {
                'description': 'Create ISO files with latest backups',
                'function': command_mkiso,
                'help-function': lambda x: (COMMAND_MKISO_HELP)
            }
        },
        'config': {
            'section': 'mkiso',
            'global': True,
            'local': True,
            'values': {
                'mkiso.directory': {
                    'option': 'directory',
                    'type': 'template',
                    'default': '${BACKUP_DIR}'
                },
                'mkiso.maxiso': {
                    'option': 'maxiso',
                    'type': 'integer',
                    'default': 7
                },
                'mkiso.all-finals': {
                    'option': 'all-finals',
                    'type': 'boolean',
                    'default': False
                }
            }
        }
        
    }

