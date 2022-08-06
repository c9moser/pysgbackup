#-*- coding:utf-8 -*-
################################################################################
# sgbackup - ftp
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

import sgbackup
#from sgbackup import plugins
from sgbackup.config import CONFIG
import gettext
import ftplib
import getopt
import glob

N_ = lambda s: (s)

def Q_(msgid):
    s = gettext.gettext(msgid)
    if s == msgid:
        if '|' in msgid:
            return msgid.split('|',1)[1]
    return s

_HELP={
    'ftp': N_('file|command.ftp.help.txt'),
    'ftp-all': N_('file|command.ftp-all.help.txt'),
    'ftp-list': N_('file|command.ftp-list.help.txt')
}

def _get_help(cmd):
    filename = os.path.join(os.path.dirname(__file__),Q_(_HELP[cmd]))
    with open(filename,'r') as ifile:
        s = ifile.read()
    return s
# _get_help()

def _ftp_cwd_directory(ftp,directory=None):
    if not directory:
        directory=CONFIG['ftp.directory']
        
    try:
        ftp.cwd(directory)
    except Exception as error:
        print(error)
        
        dirlist = directory.split('/')
        if not dirlist[0]:
            ftp.cwd('/')
            del dirlist[0]
            
        if not dirlist[-1]:
            del dirlist[-1]
            
        for i in dirlist:
            if not i:
                continue
            dir_exists = False
            for j in ftp.nlst():
                if i == j:
                    dir_exists = True
                    break
            if not dir_exists:
                ftp.mkd(i)                
            ftp.cwd(i)
# _ftp_cwd_backupdir()

def ftp_backup_files(game,filenames=[],connect={}):
    ftp_host=CONFIG['ftp.host']
    ftp_user=CONFIG['ftp.user']
    ftp_password=CONFIG['ftp.password']
    ftp_dir=CONFIG['ftp.directory']
    
    if connect:
        if 'host' in connect:
            ftp_host=connect['host']
        if 'user' in connect:
            ftp_user=connect['user']
        if 'password' in connect:
            ftp_password=connect['password']
        if 'directory' in connect:
            ftp_dir=connect['directory']

    ftp_dir = ftp_dir.replace('\\','/')
    game_dir='/'.join((ftp_dir,game.savegame_name))
    
    ftp=ftplib.FTP(ftp_host,user=ftp_user,passwd=ftp_password)
    ftp.login(ftp_user,ftp_password)
    _ftp_cwd_directory(ftp,game_dir)

    for fname in filenames:
        if CONFIG['verbose']:
            print('<ftp:put> {0}'.format(fname))
        with open(fname,'rb') as ifile:
            ftp.storbinary("STOR {0}".format(os.path.basename(fname)),fp=ifile)
        
    ftp.quit()    
# ftp_backup_files

def ftp_put_listfile(ftp,ftpdir,listfile):
    pass

def command_ftp(db,argv):
    try:
        opts,args = getopt.getopt(argv,'d:Dh:p:u:Vv', 
                                  ['directory=',
                                   'dir-mode',
                                   'host=',
                                   'password=',
                                   'user=',
                                   'no-verbose',
                                   'verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        print(_get_help('ftp'))
        sys.exit(2)
        
    if not args:
        print('[sgbackup ftp] ERROR: No GameIDs given!',file=sys.stderr)
        print(_get_help('ftp'))
        sys.exit(2)
        
    dir_mode = False
    connect={}
    for o,a in opts:
        if o == '-d' or o == '--directory':
            connect['directory'] = a
        elif o == '-D' or o == '--dir-mode':
            dir_mode = True
        elif o == '-h' or o == '--host':
            connect['host'] = a
        elif o == '-u' or '--user':
            connect['user'] = a
        elif o == '-p' or o == '--password':
            connect['password'] = a
        elif o == '-V' or o == '--no-verbose':
            CONFIG['verbose'] = False
        elif o == '-v' or o == '--verbose':
            CONFIG['verbose'] = True
            
    for game_id in args:
        if not db.has_game(game_id):
            print('No such GameID "{0}!"'.format(game_id),file=sys.stderr)
            sys.exit(2)
            
    if dir_mode:
        for game_id in args:
            game = db.get_game(game_id)
            game_dir = os.path.join(CONFIG['backup.dir'],game.savegame_name)
            backup_files = []
            for i in os.listdir(game_dir):
                if i == '.' or i == '..':
                    continue
                    
                filename = os.path.join(game_dir,i)
                if os.path.isfile(filename):
                    backup_files.append(i)
                    
            if not backup_files:
                print('[sgbackup ftp] No backup files for "{0}" found! SKIPPING!'.format(game_id))
                continue
                
            ftp_backup_files(game,backup_files,connect)                           
    else:
        for game_id in args:
            backup_files=[]
            
            game = db.get_game(game_id)
            filename = sgbackup.backup.find_latest_backup(game)
            if filename:
                backup_files.append(filename)
                extra_files = glob.glob('.'.join((filename,'*')))
                if extra_files:
                    for i in extra_files:
                        backup_files.append(i)
                        
            if not backup_files:
                print('[sgbackup ftp] No backup files for "{0}" found! SKIPPING!'.format(game_id))
                continue
                
            ftp_backup_files(game,backup_files,connect)
# command_ftp             
            
            
def command_ftp_all(db,argv):
    try:
        opts,args = getopt.getopt(argv,'Dd:h:p:u:Vv',
                                  ['dir-mode',
                                   'directory=',
                                   'host=',
                                   'password=',
                                   'user=',
                                   'no-verbose',
                                   'verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        print(_get_help('ftp-all'))
        sys.exit(2)
        
    if args:
        print('[sgbackup ftp-all] This command does not take any arguments!',file=sys.stderr)
        print(_get_help('ftp-all'))
        sys.exit(2)
        
    connect={}
    dir_mode = False
    for o,a in opts:
        if o == '-D' or o == '--dir-mode':
            dir_mode = True
        elif o == '-d' or o == '--directory':
            connect['directory'] = a
        elif o == '-h' or o == '--host':
            connect['host'] = a
        elif o == '-p' or o == '--password':
            connect['password'] = a
        elif o == '-u' or o == '--user':
            connect['user'] = a
        elif o == '-V' or o == '--no-verbose':
            CONFIG['verbose'] == False
        elif o == '-v' or o == '--verbose':
            CONFIG['verbose'] = True
            
    for game_id in db.list_game_ids():
        game = db.get_game(game_id)
        backup_files = []
        
        if dir_mode:
            game_dir = os.path.join(CONFIG['backup.dir'],game.savegame_name)
            for i in listdir(game_dir):
                if i == '.' or i == '..':
                    continue
                    
                filename = os.path.join(game_dir,i)
                if os.path.isfile(os.path.join(filename)):
                    backup_files.append(filename)
        else:
            filename = sgbackup.backup.find_latest_backup(game)
            if filename:
                backup_files.append(filename)
                for i in glob.glob('.'.join((filename,'*'))):
                    if os.path.isfile(i):
                        backup_files.append(i)
                        
        if not backup_files:
            print('[sgbackup ftp] No backups for "{0}" found! SKIPPING!'.format(game_id))
            continue
            
        ftp_backup_files(game,backup_files)
# command_ftp_all()
    
def command_ftp_list(db,argv):
    try:
        opts,args = getopt.getopt(argv,'d:h:L:p:ru:Vv',
                                  ['directory=',
                                  'host=',
                                  'password=',
                                  'listfile=',
                                  'remove',
                                  'user=',
                                  'no-verbose',
                                  'verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        print(_get_help('ftp-list'))
        sys.exit(2)
        
    if args:
        print("[sgbackup ftp-list] ERROR: This command does not take any arguments!",file=sys.stderr)
        print(_get_help('ftp-list'))
        
    connect={
        'directory': CONFIG['ftp.directory'],
        'host': CONFIG['ftp.host'],
        'user': CONFIG['ftp.user'],
        'password': CONFIG['ftp.password']
    }
    listfile = CONFIG['backup.listfile']
    remove = False
    for o,a in opts:
        if o == '-d' or o == '--directory':
            connect['directory'] = a
        elif o == '-h' or o == '--host':
            connect['host'] = a
        elif o == '-L' or o == '--listfile':
            listfile = a
        elif o == '-r' or o == '--remove':
            remove = True
        elif o == '-p' or o == '--password':
            connect['password'] = a
        elif o == '-u' or o == '--user':
            connect['user'] = a
        elif o == '-V' or o == '--no-verbose':
            CONFIG['verbose'] = False
        elif o == '-v' or o == '--verbose':
            CONFIG['verbose'] = True
    
    if not os.path.isfile(listfile):
        print('[sgbackup ftp-list] Listfile "{0}" does not exist!'.format(listfile))
        sys.exit(0)
            
    ftp=ftplib.FTP(connect['host'],user=connect['user'],password=connect['password'])
    ftp.login()
   
    
    with open(listfile,'r') as ifile:
        lines = [line.strip() for line in ifile]
        for l in lines:
            if l:
                ftp_put_listfile(ftp,connect['directory'],l)

    if remove:
        os.unlink(listfile)    
# command_ftp_list()
        

plugin = {
    'name': 'ftp',
    'description': 'Put backup-files on a FTP-Server.',
    'commands': {
        'ftp': {
            'help-function': _get_help, 
            'description': 'Put backup files for given game on a FTP-Server.',
            'function': command_ftp
        },
        'ftp-all': {
            'help-function': _get_help,
            'description': 'Put backup files for all games on a FTP-Server.',
            'function': command_ftp_all
        },
        'ftp-list': {
            'help-function': _get_help, 
            'description': 'Put backup files found in listfile on a FTP-Server.',
            'function': command_ftp_list
        }
    },
    'config': {
        'section': 'ftp',
        'global': True,
        'local': True,
        'values': {
            'ftp.user': {
                'type': 'string',
                'option': 'user',
                'default': 'anonymous'
            },
            'ftp.password': {
                'type': 'string',
                'option': 'password',
                'default': ''
            },
            'ftp.host': {
                'type': 'string',
                'option': 'host',
                'default': 'loaclahost'
            },
            'ftp.directory': {
                'type': 'string',
                'option': 'directory',
                'default': '/SaveGames'
            }
        }
    }
}
