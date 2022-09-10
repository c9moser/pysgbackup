#-*- coding:utf-8 -*-
################################################################################
# sgbackup - cksum
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
import subprocess
import gettext
import getopt
from sgbackup.config import CONFIG
from sgbackup import backup,extension,help

N_ = lambda s: (s)
def Q_(msgid):
    s = gettext.gettext(msgid)
    if msgid == s:
        if  '|' in msgid:
            return msgid.split('|',1)[1]
    return s

if sys.platform == 'win32':
    def _get_checksum_programs():
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
        usr_bin = os.path.join(root_dir,'usr','bin')
        cygpath = ""

        ret = {}
        cksum_exe = ['b2sum.exe',
                     'md5sum.exe',
                     'sha1sum.exe',
                     'sha224sum.exe',
                     'sha256sum.exe',
                     'sha384sum.exe',
                     'sha512sum.exe']
        
        if os.path.isdir(usr_bin):
            if os.path.isfile(os.path.join(usr_bin,'cygpath.exe')):
                cygpath=os.path.join(usr_bin,'cygpath.exe')
            for i in cksum_exe:
                exe = os.path.join(usr_bin,i)
                if os.path.isfile(exe):
                    ret[i[:-7]]=exe
        
        return ret
    # _get_checksum_programs()
        
else:
    def _get_checksum_programs():
        ret = {}
        cksum_exe = ['b2sum',
                     'md5sum',
                     'sha1sum',
                     'sha224sum',
                     'sha256sum',
                     'sha384sum',
                     'sha512sum']

        path = os.environ['PATH'].split(':')
        for i in cksum_exe:
            for j in path:
                if os.path.isfile(os.path.join(j,i)):
                    ret[i[:-3]] = os.path.join(j,i)
                    break
                    
        return ret
    # _get_checksum_programs()
    
CHECKSUM = _get_checksum_programs()
plugin_avilable = (len(CHECKSUM) > 0)

if plugin_avilable:
    _HELP={
        'checksum': N_('file|command.checksum.help.txt'),
        'checksum-all': N_('file|command.checksum.all.txt')
    }    

    extension.EXTENSIONS['checksum'] = {
        'description': 'Filename extensions for checksum files.',
        'extensions': list(sorted(CHECKSUM.keys()))
    }
    
    def _get_help(cmd):
        filename = os.path.join(os.path.dirname(__file__),Q_(_HELP[cmd]))
        with open(filename,'r') as ifile:
            return ifile.read()
    # _get_help()

    def find_checksum_files(filename):
        ret = []
        for i in CHECKSUM.keys():
            ckfile = '.'.join((filename,i))
            if os.path.isfile(ckfile):
                ret.append(ckfile)    
        return ret
    # find_checksum_files()
    
    def backup_callback(db,game,filename):
        if CONFIG['checksum.algorithm'] == 'None':
            return True
            
        cksum = CONFIG['checksum.algorithm']
        if cksum not in CHECKSUM:
            raise RuntimeError('<checksum> Checksum "{0}" not available!'.format(cksum),file=sys.stderr)
            return False
        
        f = os.path.basename(filename)
        cwd = os.getcwd()
        os.chdir(os.path.dirname(filename))
    
        if CONFIG['checksum.bsd-tags']:
            cmd = '"{0}" --tag "{1}"'.format(CHECKSUM[cksum],f)
        else:
            cmd = '"{0}" "{1}"'.format(CHECKSUM[cksum],f)
        
        proc = subprocess.run(cmd,capture_output=True)
        if proc.returncode != 0:
            os.chdir(cwd)
            return False
        
        fn = '.'.join((f,cksum))
        with open(fn,'wb') as ofile:
            ofile.write(proc.stdout)
            
        db.add_game_backup_extrafile(game,filename,os.path.basename(fn),True)
        os.chdir(cwd)
        return True
    # backup_callback()

    def delete_backup_callback(db,game,filename):
        for cksum in CHECKSUM.keys():
            ckfile = '.'.join((filename,cksum))
            if os.path.isfile(ckfile):
                os.unlink(ckfile)
    # delete_backup_callback()
    
    def check_checksum(game,filename,delete=False):
        cwd = os.getcwd()
        os.chdir(os.path.dirname(filename))
        
        for i in find_checksum_files(filename):
            if os.path.isfile(i):
                if CONFIG['verbose']:
                    print('<checksum:check> {0} ... '.format(i),end='')
                proc = subprocess.run('{0} --check "{1}"'.format(CHECKSUM[os.path.splitext(i)[1][1:]],os.path.basename(i)))
                if proc.returncode == 0:
                    if CONFIG['verbose']:
                        print('OK')
                else:
                    if CONFIG['verbose']:
                        print('FAILED')
                    if delete:
                        print("<checksum:delete> {0}".format(filename))
                        backup.delete_backup(game,filename)
        os.chdir(cwd)
    # check_checksum

    def command_checksum(db,argv):
        try:
            opts,args = getopt.getopt(argv,'dVv',['delete','no-verbose','verbose'])
        except getopt.GetoptError as error:
            print(error,file=sys.stderr)
            help.print_help('checksum')
            sys.exit(2)
            
        if not args:
            print('[sgabckup checksum] ERROR: No GameIDs given!',file=sys.stderr)
            help.print_help('checksum')
            sys.exit(2)
        
        for game_id in args:
            if not db.has_game(game_id):
                print('[sgbackup checksum] ERROR: No game for GameID "{0}" found!'.format(game_id),file=sys.stderr)
                sys.exit(2)
            
        delete = False
        for o,a in opts:
            if o == '-d' or o == '--delete':
                delete = True
            elif o == '-V' or o == '--no-verbose':
                CONFIG['verbose'] = False
            elif o == '-v' or o == '--verbose':
                CONFIG['verbose'] = True
                
        for game_id in args:
            game = db.get_game(game_id)
            if CONFIG['verbose']:
                print('[sgbackup checksum] Checking game "{0}"'.format(game.name))
        
            for backup_file in backup.find_backups(game):
                check_checksum(game,backup_file,delete)            
    # command_checksum()
    
    def command_checksum_all(db,argv):
        try:
            opts,args = getopt.getopt(argv,'dVv',['delete','no-verbose','verbose'])
        except getopt.GetoptError as error:
            print(error,file=sys.stderr)
            print(_get_help('cheacksum-all'))
            sys.exit(2)
            
        if args:
            print('[sgbackup checksum-all] ERROR: This command does not take any arguments!',file=sys.stderr)
            help.print_help('checksum-all')
            sys.exit(2)
        
        delete = False
        for o,a in opts:
            if o == '-d' or o == '--delete':
                delete=True
            elif o == '-V' or o == '--no-verbose':
                CONFIG['verbose'] = False
            elif o == '-v' or o == '--verbose':
                CONFIG['verbose'] = True
                
        for game_id in db.list_game_ids():
            game = db.get_game(game_id)
            
            for backup_file in backup.find_backups(game):
                check_checksum(game,backup_file,delete)
    # command_checksum_all

    plugin={
        'name': 'checksum',
        'description': 'Create/Check checksum files.',
        'backup-callback': backup_callback,
        'delete-backup-callback': delete_backup_callback,
        'version': '.'.join((str(i) for i in CONFIG['version'])),
        'config' : {
            'section': 'checksum',
            'global': True,
            'local': True,
            'values': {
                'checksum.algorithm': {
                    'type': 'string',
                    'option': 'algorithm',
                    'values': ['None'] + list(CHECKSUM.keys()),
                    'default': 'None'
                },
                'checksum.bsd-tags': {
                    'option': 'bsd-tags',
                    'type': 'boolean',
                    'default': False
                }
            }
        },
        'commands': {
            'checksum': {
                'description': 'Check checksum files against backups for given game.',
                'function': command_checksum,
                'help-function': _get_help
            },
            'checksum-all': {
                'description': 'Check checksum files against backups for all games.',
                'function': command_checksum_all,
                'help-function': _get_help
            }
        }
    }

