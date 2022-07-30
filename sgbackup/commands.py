#-*- coding:utf-8 -*-
################################################################################
# sgbackup
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

from . import config,backup,database,archivers,plugins

import sys
import os
import getopt
import gettext

def Q_(s):
    t = gettext.gettext(s)
    if (t == s):
        if ('|') in s:
            return s.split('|',1)[1]
        return s
    return t
# Q_()

_ = lambda s: gettext.gettext(s)
N_ = lambda s: (s)

_HELPFILES={
    'archiver': N_('file|command.archiver.help.txt'),
    'backup': N_('file|command.backup.help.txt'),
    'backup-all': N_('file|command.backup-all.help.txt'),
    'check': N_('file|command.check.help.txt'),
    'check-all': N_('file|command.check-all.help.txt'),
    'config': N_('file|command.config.help.txt'),
    'database': N_('file|command.database.help.txt'),
    'db': N_('file|command.database.help.txt'),
    'delete-backups': N_('file|command.delete-backups.help.txt'),
    'delete-savegames': N_('file|command.delete-savegames.help.txt'),
    'plugin': N_('file|command.plugin.help.txt'),
    'restore': N_('file|command.restore.help.txt'),
    'restore-all': N_('file|command.restore-all.help.txt'),
    'version': N_('file|command.version.help.txt'),
    'write-config': N_('file|command.write-config.help.txt')
}

def _get_command_help(command):
    def _read_helpfile(filename):
        if not os.path.isabs(filename):
            filename = os.path.join(os.path.dirname(__file__),filename)
        
        with open(filename,'r') as ifile:
            return ifile.read()
    # _read_helpfile()
    
    if command in _HELPFILES:
        file=Q_(_HELPFILES[command])
        return _read_helpfile(file)
    else:
        print('No helpfile for command "{0}" found!'.format(command),file=sys.stderr)

def _get_help():
    help="""sgbackup help

USAGE:
======
  sgbackup help [COMMAND]
  sgbackup [COMMAND] [OPTIONS] [ARGS] ...
  
COMMANDS:
=========
"""
    length=0
    for cmd in COMMANDS.keys():
        if len(cmd) > length:
            length = len(cmd)
            
    length += 1
    length = ((length // 4) + 1) * 4
    
    for cmd in sorted(COMMANDS.keys()):
        if 'description' in COMMANDS[cmd]:
            s = "  {0: <{2}}{1}\n".format(cmd,COMMANDS[cmd]['description'],length)
        else:
            s = "  {0}\n".format(cmd)
        help += s
        
    return help
# _get_help()


def command_help(db,argv):
    if len(argv) == 0:
        print(_get_help())
        return
        
    if (len(argv) > 1):
        print('[sgbackup help] ERROR: Too many arguments!',file=sys.stderr)
        print(_get_help())
        sys.exit(2)
        
    cmd = argv[0]
    if cmd not in COMMANDS:
        print('[sgbackup help] ERROR: Unknown command "{0}"!'.format(cmd),file=sys.stderr)
        print(_get_help())
        sys.exit(2)
        
    if 'help-function' in COMMANDS[cmd]:
        print(COMMANDS[cmd]['help-function'](cmd))
    elif 'help' in COMMANDS[cmd]:
        print(COMMANDS[cmd]['help'])
    else:
        print('[sgbackup help] No help for command "{0}" available!'.format(cmd))
# command_help()

def command_archiver(db,argv):
    try:
        opts,args = getopt.getopt(argv,'gv',['global','verbose'])
    except getopt.GetoptError as error:
        print("[sgbackup archiver] ERROR: {0}".format(error),file=sys.stderr)
        print(COMMANDS['archiver']['help-function']('archiver'))
        sys.exit(2)
        
    global_archivers = False
    for o,a in opts:
        if o == '-g' or o == '--global':
            global_archivers = True
        if o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
            
    if not args:
        print("[sgbackup archiver] ERROR: No command given!",file=sys.stderr)
        print(COMMANDS['archiver']['help-function']('archiver'))
        sys.exit(2)
        
    if len(args) > 1:
        print("[sgbackup archiver] ERROR: Too many arguments!",file=sys.stderr)
        print(COMMANDS['archiver']['help-function']('archiver'))
        sys.exit(2)
        
    cmd = args[0]
    if cmd == 'list':
        for i in archivers.list_archivers():
            print(i)
    elif cmd == 'update':
        archivers.update(global_archivers)
    else:
        print('[sgbackup archiver] ERROR: Unknown command "{0}"!'.format(cmd),file=sys.stderr)
        print(COMMANDS['archiver']['help-function']('archiver'))
        sys.exit(2)
# command_archiver

def command_backup(db,argv):
    try:
        opts,args = getopt.getopt(argv, 
                                  "FfL:Wwv",
                                  ["final",
                                   "listfile=",
                                   "no-final",
                                   "no-write-listfile",
                                   "verbose",
                                   "write-listfile"])
    except getopt.GetoptError as err:
        print(err,file=sys.stderr)
        print(COMMANDS['backup']['help-function']('backup'))
        sys.exit(2)
    
    final_backup = False
    remove_final_backup_flag = False
    for o,a in opts:
        if (o == '-F' or o == '--no-final'):
            final_backup = False
            remove_final_backup_flag = True
        elif (o == '-f' or o == '--final'):
            final_backup = True
        elif (o == '-L' or o == '--listfile'):
            config.CONFIG['backup.write-listfile']=True
            config.CONFIG['backup.listfile']=a
        elif (o == '-v' or o == '--verbose'):
            config.CONFIG['verbose']=True
        elif (o == '-W' or o == '--no-write-listfile'):
            config.CONFIG['backup.write-listfile']=False
        elif (o == '-w' or o == '--write-listfile'):
            config.CONFIG['backup.write_listfile']=True
            
    if not args:
        print("[sgbackup backup] No GameIDs given!",file=sys.stderr)
        print(COMMANDS['backup']['help-function']('backup'))
        sys.exit(2)
        
    games=[]
    for i in args:
        g = db.get_game(i)
        if not g:
            print("[sgbackup backup]: Unknown GameID '{0}'!".format(i),file=sys.stderr)
            print("Use 'sgbackup database list' to show known GameIDs.",file=sys.stderr)
            sys.exit(2)
        games.append(g)
        
    for g in games:
        if final_backup:
            g.final_backup=True
            db.add_game(g)
        elif not final_backup and remove_final_backup_flag:
            g.final_backup=False
            db.add_game(g)

        backup.backup(g,config.CONFIG['backup.listfile'],config.CONFIG['backup.write-listfile'])
# command_backup()

def command_backup_all(db,argv):
    try:
        opts,args = getopt.getopt(argv,'fL:vWw',
                                  ['force',
                                   'listfile=',
                                   'no-write_listfile',
                                   'verbose',
                                   'write-listfile'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        print(COMMANDS['backup-all']['help-function']('backup-all'))
        sys.exit(2)
    
    if args:
        print('sgbackup backup-all takes no arguments!',file=sys.stderr)
        print(COMMANDS['backup-all']['help-function']('backup-all'))
        sys.exit(2)
        
    force = False
    listfile = config.CONFIG['backup.listfile']
    write_listfile = config.CONFIG['backup.write-listfile']
    for o,a in opts:
        if o == '-f' or o == '--force':
            force = True
        elif o == '-L' or o == '--listfile':
            listfile = a
        elif o == '-W' or o == '--no-write-listfile':
            write_listfile = False
        elif o == '-w' or o == '--write-listfile':
            write_listfile = True
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
            
    backup.backup_all(db,listfile,write_listfile,force)
# command_backup_all()

def command_config(db,argv):
    try:
        opts,args = getopt.getopt(argv,'gsv',['global','show','verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        print(COMMANDS['config']['help-function']('config'))
        sys.exit(2)
        
    global_config = False
    show = False
    for o,a in opts:
        if o == '-g' or o == '--global':
            global_config = True
        elif o == '-s' or o == '--show':
            show = True
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
            
    if not args:
        config.print_config(global_config)
    elif len(args) == 1:
        if show:
            try:
                config.print_config_value(args[0],global_config)
            except Exception as error:
                print('[sgbackup config] ERROR: {0}'.format(error),file=sys.stderr)
                sys.exit(2)
        else:
            try:
                config.print_config_key(args[0],global_config)
            except Exception as error:
                print('[sgbackup config] ERROR: {0}'.format(error),file=sys.stderr)
                sys.exit(2)
    elif len(args) == 2:
        try:
            config.write_config_key(args[0],args[1],global_config)
        except getopt.GetoptError as error:
            print('[sgbackup config] ERROR: {0}'.format(error),file=sys.stderr)
    else:
        print('[sgbackup config] ERROR: Too many arguments!',file=sys.stderr)
        print(COMMANDS['config']['help-function']('config'))
        sys.exit(2)
# command_config()

def command_check(db,argv):
    try:
        opts,args = getopt.getopt(argv,'AaCcdv',
                                  ['ask',
                                  'no-ask',
                                  'create-missing',
                                  'check-deleted',
                                  'remove-deleted',
                                  'verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        print(COMMANDS['check']['help-function']('check'))
        sys.exit(2)    
    
    if not args:
        print('[sgbackup check] ERROR: No GameIDs given!',file=sys.stderr)
        print(COMMANDS['check']['help-function']('check'))
        sys.exit(2)
        
    ask = True
    create_missing = False
    check_deleted = False
    delete_failed = False
    
    for o,a in opts:
        if o == '-a' or o == '--ask':
            ask = True
        elif o == '-A' or o == '--no-ask':
            ask = False
        elif o == '-c' or o == '--create-missing':
            create_missing = True
        elif o == '-C' or o == '--check-deleted':
            check_deleted = True
        elif o == '-d' or o == '--delete-failed':
            delete_failed = True
            ask = False
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
            
    for game_id in args:
        if not db.has_game(game_id):
            print('[sgbackup check] No such GameID "{0}"!'.format(game_id),file=sys.stderr)
            print(COMMANDS['check']['help-function']('check'))
            sys.exit(2)
            
    for game_id in args:
        game = db.get_game(game_id)
        backup.check(game,create_missing,check_deleted,delete_failed,ask)
# command_check()
    
def command_check_all(db,argv):
    try:
        opts,args = getopt.getopt(argv,'AaCcdv', 
                                  ['ask',
                                   'no-ask'
                                   'create-missing',
                                   'check-deleted',
                                   'delete-failed',
                                   'verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        print(COMMANDS['check-all']['help-function']('check-all'))
        sys.exit(2)
        
    if len(args) > 0:
        print('[sgbackup check-all] ERROR: This command does not handle any arguments!',file=sys.stderr)
        print(COMMANDS['check-all']['help-function']('check-all'))
        sys.exit(2)
        
    ask=True
    create_missing=False
    check_deleted=False
    delete_failed=False
    
    for o,a in opts:
        if o == '-a' or o == '--ask':
            ask = True
        elif o == '-A' or o == '--no-ask':
            ask = False
        elif o == '-C' or o == '--check-deleted':
            check_deleted = True
        elif o == '-c' or o == '--create-missing':
            create_missing = True
        elif o == '-d' or o == '--delete-failed':
            delete_failed = True
            ask = False
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
    
    for game_id in db.list_game_ids():
        game = db.get_game(game_id)
        backup.check(game,create_missing,check_deleted,delete_failed,ask)
# command_check_all()

def command_database(db,argv):
    commands=[
        'delete',
        'list',
        'list-ids',
        'list-names',
        'name',
        'show',
        'update']
    
    if not argv:
        print("sgbackup database: No command given!", file=sys.stderr)
        print(COMMANDS['database']['help-function']('database'))
    if (argv[0]) not in commands:
        print("sgbackup database: Unknown command '{0}'!".format(argv[0]),file=sys.stderr)
        print(COMMANDS['database']['help-function']('database'))
    
    try:   
        opts,args = getopt.getopt(argv[1:], 'fv', ['force','verbose'])
    except getopt.GetoptError as err:
        print(err,file=sys.stderr)
        print(COMMANDS['database']['help-function']('database'))
        sys.exit(2)
   
    force=False
    for opt,value in opts:
        if opt == '-f' or opt == '--force':
            force = True
        elif opt == '-v' or opt == '--verbose':
            config.CONFIG['verbose'] = True
    
    cmd = argv[0]
    if cmd == 'delete':
        if not args:
            print("sgbackup database delete: No GameIDs given!'",file=sys.stderr)
            print(COMMANDS['database']['help-function']('database'))
            sys.exit(2)
        
        for i in args:
            if not db.has_game(i):
                print("No Game found for GameID '{0}'!".format(i),file=sys.stderr)
                sys.exit(2)
                
        for i in args:
            if (config.CONFIG['verbose']):
                g = db.get_game(i)
                print('[database:delete] {0}'.format(g.name))
            db.delete_game(i)            
    elif cmd == 'list':
        game_list = db.list_games()
        max_len = 0
        for gid,name in game_list:
            if len(gid) > max_len:
                max_len = len(gid)
        if (max_len + 1) > 32:
            max_len = 32
        else:
            max_len += 1
            
        for gid,name in game_list:
            if len(gid) < max_len:
                s=gid + (" " * (max_len - len(gid))) + name
            else:
                s=" ".join((gid,name))
            print(s)
    elif cmd == 'list-ids':
        for gid in db.list_game_ids():
            print(gid)        
    elif cmd == 'list-names':
        for name in db.list_game_names():
            print(name)
    elif cmd == 'name':
        if not args:
            print("sgbackup database name: No GameIDs given!",file=sys.stderr)
            print(COMMANDS['database']['help-function']('database'))
            sys.exit(2)
        for gid in args:
            if not db.has_game(gid):
                print("No GameID '{0}' found!".format(gid),file=sys.stderr)
                sys.exit(2)
        for gid in args:
            game = db.get_game(gid)
            print(game.name) 
    elif cmd == 'show':
        if not args:
            print('sgbackup database show: No GameIDs given!',file=sys.stderr)
            print(COMMANDS['database']['help-function']('database'))
            sys.exit(2)
        for gid in args:
            if not db.has_game(gid):
                print('No GameID \'{0}\' found!'.format(gid))
                sys.exit(2)
        for gid in args:
            g = db.get_game(gid)
            fmt='{0}={1}'
            print(fmt.format('name',g.name))
            print(fmt.format('id',g.id))
            print(fmt.format('game-id',g.game_id))
            print(fmt.format('savegame-name',g.savegame_name))
            print(fmt.format('savegame-root',g.savegame_root))
            print(fmt.format('savegame-dir',g.savegame_dir))
    elif cmd == 'update':
        if not args:
            database.update(db,force)
        else:
            game_list=[]
            for gid in args:
                g=games.parse_gameconf(gid)
                if g:
                    game_list.append(g)
                else:
                    print("No '{0}.conf' file found!".format(gid),file=sys.stderr)
                    exit(2)
                    
            for g in game_list:
                db.add_game(g)
# command_database()

def command_delete_backups(db,argv):
    try:
        opts,args = getopt.getopt(argv,'fv',['force','verbose'])
    except getopt.GetoptError as error:
        print('[sgbackup delete-backups] ERROR: {0}'.format(error),file=sys.stderr)
        print(COMMANDS['delete-backups']['help-function']('delete-backups'))
        sys.exit(2)
        
    if not args:
        print('[sgbackup delete-backups] ERROR: No GameIDs given!',file=sys.stderr)
        print(COMMANDS['delete-backups']['help-function']('delete-backups'))
    
    keep_latest = True
    for o,a in opts:
        if o == '-f' or o == '--force':
            keep_latest = False
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
            
    for game_id in args:
        if not db.has_game(game_id):
            print('[sgbackup delete-backups] ERROR: No such GameID "{0}!"'.format(game_id))
            sys.exit(2)
            
    for game_id in args:
        game = db.get_game(game_id)
        backup.delete_backups(game,keep_latest)
# command_delete_backups

def command_delete_savegames(db,argv):
    try:
        opts,args = getopt.getopt(argv,'v',['verbose'])
    except getopt.GetoptError as error:
        print('[sgbackup delete-savegames] ERROR: {0}'.format(error),file=sys.stderr)
        print(COMMANDS['delete-savegames']['help-function']('delete-savegames'))
        sys.exit(2)
        
    if not args:
        print('[sgbackup delete-savegames] ERROR: No GameIDs given!',file=sys.stderr)
        print(COMMANDS['delete-savegames']['help-function']('delete-savegames'))
        
    for o,a in opts:
        if o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
        
    for game_id in args:
        if not db.has_game(game_id):
            print('[sgbackup delete-savegames] ERROR: No such GameID "{0}"!'.format(game_id))
            sys.exit(2)
    
    for game_id in args:
        game = db.get_game(game_id)
        backup.delete_savegames(game)
# command_delete_savegames()

def command_plugin(db,argv):
    if not argv:
        print('[sgbackup plugin] No command given!',file=sys.stderr)
        print(COMMANDS['plugin']['help-function']('plugin'))
        
    cmd = argv[0]
    if cmd == 'list':
        length = 0
        for i in plugins.get_plugins():
            if len(i) > length:
                length = len(i)
        
        length += 1
        length = ((length // 4) + 1) * 4
        
        if length > 32:
            length = 32
            
        for i in plugins.get_plugins():
            plugin = plugins.PLUGINS[i]
            
            if (len(i) < length):
                s= i + " " * (length - len(i)) + plugin.description
            else:
                s = i + " " + plugin.description
                
            print(s)
    elif cmd == 'enable':
        if len(argv) < 2:
            print("[spbackup plugin enable] ERROR: No Plugins given!",file=sys.stderr)
            print(COMMANDS['plugin']['help-function']('plugin'))
        for i in argv[1:]:
            if i not in plugins.PLUGINS:
                print('No plugin "{0} found!"'.format(i),file=sys.stderr)
                                
        for i in argv[1:]:
            db.enable_plugin(i)
    elif cmd == 'disable':
        if len(argv) < 2:
            print("[spbackup plugin disable] ERROR: No Plugins given!",file=sys.stderr)
            print(COMMANDS['plugin']['help-function']('plugin'))
        for i in argv[1:]:
            db.disable_plugin(i)
    else:
        print('[sgbackup plugin] No such command "{0}"!'.format(cmd),file=sys.stderr)
        print(COMMANDS['plugin']['help-function']('plugin'))
# command_plugin
        
    
def command_restore(db,argv):
    try:
        opts,args = getopt.getopt(argv,'cv',['choose','verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        print(COMMANDS['restore']['help-function']('restore'))
        sys.exit(2)
    
    if not args:
        print("[sgbackup restore] No GameIDs given!",file=sys.stderr)
        print(COMMANDS['restore']['help-function']('restore'))
        sys.exit(2)
    
    for game_id in args:
        if not db.has_game(game_id):
            print("[sgbackup restore] No game for GameID '{0}' found!".format(game_id))
            sys.exit(2)
                
    choose = False
    for o,a in opts:
        if o == '-c' or o == '--choose':
            choose = True
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
            
    for game_id in args:
        game = db.get_game(game_id)
        latest_backup = backup.find_latest_backup(game)
        if not latest_backup:
            print("[sgbackup restore] No SaveGame for \"{0}\" found!".format(game.name))
            continue
            
        if choose:
            backup.restore_ask(game)
        else:
            print("[sgbackup restore] {0}".format(game.name))
            backup.restore(game,latest_backup)
# command_restore()

def command_restore_all(db,argv):
    try:
        opts,args = getopt.getopt(argv,'v', ['--verbose'])
    except getopt.GetoptError as error:
        print(error, file=sys.stderr)
        print(COMMANDS['restore-all']['help-function']('restore-all'))
        
    if args:
        print("[sgbackup restore-all] Command does not take any arguments!",file=sys.stderr)
        print(COMMANDS['restore-all']['help-function']('restore-all'))
        
    for o,a in opts:
        if o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
    
    backup.restore_all(db)
# command_restore_all()

def command_version(db,argv):
    print("sgbackup {0}".format('.'.join((str(i) for i in config.CONFIG['version']))))
# command_version

def command_write_config(db,argv):
    try:
        opts,args = getopt.getopt(argv, 'gv', ['global','verbose'])
    except GetoptError as error:
        print(error,file=sys.stderr)
        print(COMMANDS['write-config']['help-function']('write-config'))
        sys.exit(2)
            
    global_config = False
    
    for o,v in opts:
        if o == '-g' or o == '--global':
            global_config=True
        if o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
            
    if not args:
        if global_config:
            filename = config.CONFIG['global-config']
        else:
            filename = config.CONFIG['user-config']
            
        if config.CONFIG['verbose']:
            print('[sgbackup write-config] {0}'.format(filename))
        try:
            config.write_config(filename,global_config)
        except Exception as error:
            print('Writing Config \'{0}\' failed! ({1})'.format(filename,error),file=sys.stderr)          
    else:
        for i in args:
            if config.CONFIG['verbose']:
                print('[sgbackup write-config] {0}'.format(i))
            try: 
                config.write_config(i,global_config)
            except Exception as error:
                print('Writing Config \'{0}\' failed! ({1})'.format(i,error),file=sys.stderr)
# command_write_config()

COMMANDS={
    'archiver': {
        'description': 'List or update known archviers.',
        'help-function': _get_command_help,
        'function':command_archiver
    },
    'backup': {
        'description': 'Backup savegames.',
        'help-function': _get_command_help,
        'function':command_backup
    },
    'backup-all': {
        'description': 'Backup all savegames.',
        'help-function': _get_command_help,
        'function':command_backup_all
    },
    'check': {
        'description': 'Perform checksum checks on backups.',
        'help-function': _get_command_help,
        'function':command_check
    },
    'check-all': {
        'description': 'Perform checksum checks on all backups.',
        'help-function': _get_command_help,
        'function': command_check_all
    },
    'config': {
        'description': 'Get/Set configuration values.',
        'help-function':_get_command_help,
        'function':command_config
    },
    'database': {
        'description': 'Perform database operations. (same as \'db\')',
        'help-function':_get_command_help,
        'function':command_database
    },
    'db': {
        'description': 'Perform database operations. (same as \'database\')',
        'help-function':_get_command_help,
        'function':command_database
    },
    'delete-backups': {
        'description': 'Delete savegame backups.',
        'help-function': _get_command_help, 
        'function': command_delete_backups
    },
    'delete-savegames': {
        'description': 'Delete savegames.',
        'help-function': _get_command_help,
        'function': command_delete_savegames
    },
    'help': {
        'description': 'Print help messages.',
        'help-function': lambda x: _get_help(),
        'function': command_help
    },
    'plugin': {
        'description': 'List/Enable/Disable plugins.',
        'help-function' : _get_command_help,
        'function': command_plugin
    },
    'restore': {
        'description': 'Restore savegames from backup.',
        'help-function': _get_command_help,
        'function': command_restore
    },
    'restore-all': {
        'description': 'Restore all savegames from backups.',
        'help-function': _get_command_help,
        'function': command_restore_all
    },
    'version': {
        'description': 'Get version information',
        'help-function':_get_command_help,
        'function':command_version
    },
    'write-config': {
        'description': 'Write a configuration file.',
        'help-function': _get_command_help,
        'function': command_write_config
    }
}

