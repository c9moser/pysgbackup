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
from sgbackup import help
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
    'ftp-list': N_('file|command.ftp-list.help.txt'),
    'fpt-listfile': N_('file|command.ftp-listfile.help.txt')
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

def ftp_backup_file(db,game,filename,connect={}):
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
    
    ftp=ftplib.FTP(ftp_host)
    ftp.login(ftp_user,ftp_password)
    _ftp_cwd_directory(ftp,game_dir)

    if os.path.isfile(filename):
        print('<ftp:put> {0}'.format(filename))            
        with open(filename,'rb') as ifile:
            ftp.storbinary("STOR {0}".format(os.path.basename(filename)),fp=ifile)
        db.set_game_backup_ftp_transferred(game,fname,True)
        
        backupfile = db.get_game_backup(game,os.path.basename(fname))
        if backupfile:
            for extrafile in backupfile['extrafiles']:
                if os.path.isabs(extrafile['filename']):
                    efname = extrafile['filename']
                else:
                    efname = os.path.join(CONFIG['backup.dir'],game.savegame_name,efname)
                
                with open(efname,'rb') as ifile:
                    ftp.storbinary("STOR {0}".format(os.path.basename(efname)),fp=ifile)
                db.set_game_backup_extrafile_ftp_transferred(game,os.path.basename(fname),extrafile['filename'],True)
    ftp.quit()    
# ftp_backup_files

def ftp_put_listfile(ftp,ftpdir,listfile):
    pwd = ftp.pwd()
    directory = '/'.join((ftpdir,os.path.dirname(listfile)))
    directory = directory.replace('\\','/')

    try:
        ftp.cwd(directory)
    except Exception as error:
        dirs = directory.split('/')
        if not dirs[0]:
            ftp.cwd('/')
            del dirs[0]
        if not dirs[-1]:
            del dirs[-1]
            
        for d in dirs:
            dir_found = False
            if not d:
                continue
            if d in ftp.nlst():
                dir_found=True
                
            if not dir_found:
                ftp.mkd(d)
            ftp.cwd(d)
    
    filename = os.path.join(CONFIG['backup.dir'],listfile)
    if os.path.isfile(filename):
        with open(filename,'rb') as ifile:
            print('<ftp:put> {}'.format(filename))
            ftp.storbinary("STOR {0}".format(os.path.basename(filename)),fp=ifile)
            
    ftp.cwd(pwd)

def command_ftp_list(db,argv):
    try:
        opts,args = getopt.getopt(argv,'d:h:p:u:Vv',
                                  ['directory='
                                   'host=',
                                   'password=',
                                   'user=',
                                   'no-verbose',
                                   'verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        help.print_help('ftp-list')
        
    if args:
        print('[sgbackup ftp-list] Command does not take any arguments!',file=sys.stderr)
        help.print_help('ftp-list')
        
    connect = {
        'directory': CONFIG['ftp.directory'],
        'host': CONFIG['ftp.host'],
        'user': CONFIG['ftp.user'],
        'password': CONFIG['ftp.password']
    }
    
    for o,a in opts:
        if o == '-d' or o == '--directory':
            connect['directory'] = a
        elif o == '-h' or o == '--host':
            connect['host'] = a
        elif o == '-p' or o == '--password':
            connect['password'] = a
        elif o == '-u' or o == '--user':
            connect['user'] = a
        elif o == '-v' or o == '--verbose':
            CONFIG['verbose'] = True
        elif o == '-V' or o == '--no-verbose':
            CONFIG['verbose'] = False
            
    for game_id in db.list_game_ids():
        game = db.get_game(game_id)
        for game_backup in db.get_game_backups(game):
            if game_backup['use_ftp'] and not game_backup['ftp_transferred']:
                fname = os.path.join(CONFIG['backup.dir'],game.savegame_name,game_backup['filename'])
                ftp_backup_file(db,game,fname,connect)
# command_ftp_list
    
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
        help.print_help('ftp')
        sys.exit(2)
        
    if not args:
        print('[sgbackup ftp] ERROR: No GameIDs given!',file=sys.stderr)
        help.print_help('ftp')
        sys.exit(2)
        
    dir_mode = False
    connect={
        'host': CONFIG['ftp.host'],
        'user': CONFIG['ftp.user'],
        'password': CONFIG['ftp.password'],
        'directory': CONFIG['ftp.directory']
    }
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
            if not (game_dir):
                continue
                
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
                
            for bf in backup_files:
                ftp_backup_file(db,game,bf,connect)
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
                
            for bf in backup_files:
                ftp_backup_file(db,game,bf,connect)
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
        help.print_help('ftp-all')
        sys.exit(2)
        
    if args:
        print('[sgbackup ftp-all] This command does not take any arguments!',file=sys.stderr)
        help.print_help('ftp-all')
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
            if not os.path.isdir(game_dir):
                continue
                
            for i in os.listdir(game_dir):
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
            
        for bf in backup_files:
            ftp_backup_file(db,game,bf,connect)
# command_ftp_all()
    
        

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
            'description': 'Put backup files from filelist in database on an FTP-Server',
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
