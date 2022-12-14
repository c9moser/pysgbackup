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

from . import config,help,backup,database,archivers,extension,plugins,games

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
    'extension': N_('file|command.extension.help.txt'),
    'game': N_('file|command.game.help.txt'),
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
        help.print_help()
        return
        
    if (len(argv) > 1):
        print('[sgbackup help] ERROR: Too many arguments!',file=sys.stderr)
        help.print_help()
        return 2
        
    cmd = argv[0]
    if cmd not in COMMANDS:
        print('[sgbackup help] ERROR: Unknown command "{0}"!'.format(cmd),file=sys.stderr)
        help.print_help()
        return 2
    help.print_help(cmd)
    return 0
# command_help()

def command_archiver(db,argv):
    try:
        opts,args = getopt.getopt(argv,'gvV',['global','verbose','no-verbose'])
    except getopt.GetoptError as error:
        print("[sgbackup archiver] ERROR: {0}".format(error),file=sys.stderr)
        help.print_help('archiver')
        return 2
        
    global_archivers = False
    for o,a in opts:
        if o == '-g' or o == '--global':
            global_archivers = True
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
        elif o == '-V' or o == '--no-verbose':
            config.CONFIG['verbose'] = False
            
    if not args:
        print("[sgbackup archiver] ERROR: No command given!",file=sys.stderr)
        help.print_help('archiver')
        return 2
        
    if len(args) > 1:
        print("[sgbackup archiver] ERROR: Too many arguments!",file=sys.stderr)
        help.print_help('archiver')
        return 2
        
    cmd = args[0]
    if cmd == 'list':
        for i in archivers.list_archivers():
            print(i)
    elif cmd == 'update':
        archivers.update_archivers(global_archivers)
    else:
        print('[sgbackup archiver] ERROR: Unknown command "{0}"!'.format(cmd),file=sys.stderr)
        help.print_help('archiver')
        return 2
        
    return 0
# command_archiver

def command_backup(db,argv):
    try:
        opts,args = getopt.getopt(argv, 
                                  "FfVv",
                                  ["final",
                                   "no-final",
                                   "verbose",
                                   "no-verbose"])
    except getopt.GetoptError as err:
        print(err,file=sys.stderr)
        help.print_help('backup')
        return 2
    
    final_backup = False
    remove_final_backup_flag = False
    for o,a in opts:
        if (o == '-F' or o == '--no-final'):
            final_backup = False
            remove_final_backup_flag = True
        elif (o == '-f' or o == '--final'):
            final_backup = True
        elif (o == '-V' or o == '--no-verbose'):
            config.CONFIG['verbose'] = False
        elif (o == '-v' or o == '--verbose'):
            config.CONFIG['verbose']=True
        
            
    if not args:
        print("[sgbackup backup] No GameIDs given!",file=sys.stderr)
        help.print_help('backup')
        return 2
        
    games=[]
    for i in args:
        g = db.get_game(i)
        if not g:
            print("[sgbackup backup]: Unknown GameID '{0}'!".format(i),file=sys.stderr)
            print("Use 'sgbackup database list' to show known GameIDs.",file=sys.stderr)
            return 2
        games.append(g)
        
    for g in games:
        if final_backup:
            g.final_backup=True
            db.add_game(g)
        elif not final_backup and remove_final_backup_flag:
            if g.final_backup:
                backup.unfinal(db,g)


        backup.backup(db,g)
    return 0
# command_backup()

def command_backup_all(db,argv):
    try:
        opts,args = getopt.getopt(argv,'fVv',
                                  ['force',
                                   'verbose',
                                   'no-verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        help.print_help('backup-all')
        return 2
    
    if args:
        print('sgbackup backup-all takes no arguments!',file=sys.stderr)
        help.print_help('backup-all')
        return 2
        
    force = False
    for o,a in opts:
        if o == '-f' or o == '--force':
            force = True
        elif o == '-V' or o == '--no-verbose':
            config.CONFIG['verbose'] = False
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
            
    backup.backup_all(db,force)
    return 0
# command_backup_all()

def command_config(db,argv):
    try:
        opts,args = getopt.getopt(argv,'gsVv',['global','show','verbose','no-verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        help.print_help('config')
        return 2
        
    global_config = False
    show = False
    for o,a in opts:
        if o == '-g' or o == '--global':
            global_config = True
        elif o == '-s' or o == '--show':
            show = True
        elif o == '-V' or o == '--no-verbose':
            config.CONFIG['verbose'] = False
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
                return 2
        else:
            try:
                config.print_config_key(args[0],global_config)
            except Exception as error:
                print('[sgbackup config] ERROR: {0}'.format(error),file=sys.stderr)
                return 2
    elif len(args) == 2:
        try:
            config.write_config_key(args[0],args[1],global_config)
        except getopt.GetoptError as error:
            print('[sgbackup config] ERROR: {0}'.format(error),file=sys.stderr)
    else:
        print('[sgbackup config] ERROR: Too many arguments!',file=sys.stderr)
        help.print_help('config')
        return 2
        
    return 0
# command_config()

def command_check(db,argv):
    try:
        opts,args = getopt.getopt(argv,'CcdVv',
                                  ['create-missing',
                                   'check-deleted',
                                   'remove-deleted',
                                   'no-verbose',
                                   'verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        help.print_help('check')
        return 2
    
    if not args:
        print('[sgbackup check] ERROR: No GameIDs given!',file=sys.stderr)
        help.print_help('check')
        return 2
        
    ask = True
    create_missing = False
    check_deleted = False
    delete_failed = False
    
    for o,a in opts:
        if o == '-c' or o == '--create-missing':
            create_missing = True
        elif o == '-C' or o == '--check-deleted':
            check_deleted = True
        elif o == '-d' or o == '--delete-failed':
            delete_failed = True
            ask = False
        elif o == '-V' or o == '--no-verbose':
            config.CONFIG['verbose'] = False
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
            
    for game_id in args:
        if not db.has_game(game_id):
            print('[sgbackup check] No such GameID "{0}"!'.format(game_id),file=sys.stderr)
            help.print_help('check')
            return 2
            
    for game_id in args:
        game = db.get_game(game_id)
        backup.check(db,game,create_missing,check_deleted,delete_failed)
        
    return 0
# command_check()
    
def command_check_all(db,argv):
    try:
        opts,args = getopt.getopt(argv,'CcdVv', 
                                  ['create-missing',
                                   'check-deleted',
                                   'delete-failed',
                                   'no-verbose',
                                   'verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        help.print_help('check-all')
        return 2
        
    if len(args) > 0:
        print('[sgbackup check-all] ERROR: This command does not handle any arguments!',file=sys.stderr)
        help.print_help('check-all')
        return 2
        
    ask=True
    create_missing=False
    check_deleted=False
    delete_failed=False
    
    for o,a in opts:
        if o == '-C' or o == '--check-deleted':
            check_deleted = True
        elif o == '-c' or o == '--create-missing':
            create_missing = True
        elif o == '-d' or o == '--delete-failed':
            delete_failed = True
            ask = False
        elif o == '-V' or o == 'no-verbose':
            config.CONFIG['verbose'] = False
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
    
    for game_id in db.list_game_ids():
        game = db.get_game(game_id)
        backup.check(db,game,create_missing,check_deleted,delete_failed)
        
    return 0
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
        help.print_help('database')
        return 2
    if (argv[0]) not in commands:
        print("sgbackup database: Unknown command '{0}'!".format(argv[0]),file=sys.stderr)
        help.print_help('database')
        return 2
    
    try:   
        opts,args = getopt.getopt(argv[1:], 'fVv', ['force','verbose','no-verbose'])
    except getopt.GetoptError as err:
        print(err,file=sys.stderr)
        help.print_help('database')
        return 2
   
    force=False
    for o,a in opts:
        if o == '-f' or o == '--force':
            force = True
        elif o == '-V' or o == '--no-verbose':
            config.CONFIG['verbose'] = False
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
    
    cmd = argv[0]
    if cmd == 'delete':
        if not args:
            print("sgbackup database delete: No GameIDs given!'",file=sys.stderr)
            help.print_help('database')
            return 2
        
        for i in args:
            if not db.has_game(i):
                print("No Game found for GameID '{0}'!".format(i),file=sys.stderr)
                return 2
                
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
            help.print_help('database')
            return 2
        for gid in args:
            if not db.has_game(gid):
                print("No GameID '{0}' found!".format(gid),file=sys.stderr)
                return 2
        for gid in args:
            game = db.get_game(gid)
            print(game.name) 
    elif cmd == 'show':
        if not args:
            print('sgbackup database show: No GameIDs given!',file=sys.stderr)
            help.print_help('database')
            return 2
        for gid in args:
            if not db.has_game(gid):
                print('No GameID \'{0}\' found!'.format(gid))
                return 2
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
    return 0
# command_database()

def command_delete_backups(db,argv):
    try:
        opts,args = getopt.getopt(argv,'fVv',['force','verbose','no-verbose'])
    except getopt.GetoptError as error:
        print('[sgbackup delete-backups] ERROR: {0}'.format(error),file=sys.stderr)
        help.print_help('delete-backups')
        return 2
        
    if not args:
        print('[sgbackup delete-backups] ERROR: No GameIDs given!',file=sys.stderr)
        help.print_help('delete-backups')
    
    keep_latest = True
    for o,a in opts:
        if o == '-f' or o == '--force':
            keep_latest = False
        elif o == '-V' or o == '--no-verbose':
            config.CONFIG['verbose'] = False
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
            
    for game_id in args:
        if not db.has_game(game_id):
            print('[sgbackup delete-backups] ERROR: No such GameID "{0}!"'.format(game_id))
            return 2
            
    for game_id in args:
        game = db.get_game(game_id)
        backup.delete_backups(db,game,keep_latest)
        
    return 0
# command_delete_backups

def command_delete_savegames(db,argv):
    try:
        opts,args = getopt.getopt(argv,'Vv',['no-verbose','verbose'])
    except getopt.GetoptError as error:
        print('[sgbackup delete-savegames] ERROR: {0}'.format(error),file=sys.stderr)
        help.print_help('delete-savegames')
        return 2
        
    if not args:
        print('[sgbackup delete-savegames] ERROR: No GameIDs given!',file=sys.stderr)
        help.print_help('delete-savegames')
        
    for o,a in opts:
        if o == '-V' or o == '--no-verbose':
            config.CONFIG['verbose'] = False
        if o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
        
    for game_id in args:
        if not db.has_game(game_id):
            print('[sgbackup delete-savegames] ERROR: No such GameID "{0}"!'.format(game_id))
            return 2
    
    for game_id in args:
        game = db.get_game(game_id)
        backup.delete_savegames(game)
    return 0
# command_delete_savegames()

def command_extension(db,argv):
    if not argv:
        length=0
        
        for name in extension.EXTENSIONS.keys():
            if len(name) > length:
                length=len(name)
                
        if length > 32:
            length = 32
            
        length = (((length // 4) + 1) * 4)
        
        for name,ext in extension.EXTENSIONS.items():
            if 'description' in ext:
                if (len(name) < length):
                    print(name + (' ' * (length - len(name))) + ext['description'])
                else:
                    print('{} {}'.format(name,ext['description']))    
            else:
                print(name)
    else:
        for name in argv:
            try:
                for e in extension.get_extensions(name):
                    print(e)
            except LookupError as error:
                print('[sgbackup extension] ERROR: {}'.format(err))
                return 2
    return 0
# command_extension

def command_game(db,argv):
    commands = ['add','list','remove','show']
    
    if not argv:
        help.print_help('game')
        return 2
    
    cmd = argv[0]
    
    if not cmd in commands:
        print('[sgbackup game] ERROR: Unknown command "{0}"!'.format(cmd),file=sys.stderr)
        help.print_help('game')
        return 2
        
    try:
        opts,args = getopt.getopt(argv[1:],'fVv',['force','no-verbose','verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        help.print_help('game')
        return 2
    
    force = False
    for o,a in opts:
        if o == '-f' or o == '--force':
            force = True
        elif o == '-V' or o == '--no-verbose':
            config.CONFIG['verbose'] = False
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
            
    if cmd == 'list':
        gameconf_dirs = games.get_conf_dirs()
        game_ids = []
        game_list=[]
        for d in gameconf_dirs:
            for f in os.listdir(d):
                if f.startswith('.') or f.startswith('_'):
                    continue
                if f.endswith('.game'):
                    gid = f[:-5]
                    if gid not in game_ids:
                        game_ids.append(gid)
        for gid in sorted(game_ids):
            game = games.parse_gameconf(gid)
            if game:
                game_list.append(game)
                
        gid_len = 0
        for game in game_list:
            length = len(game.game_id)
            if length > gid_len:
                gid_len = length
                
        for game in game_list:
            if db.has_game(game.game_id):
                x = '+'
            else:
                x = '-'
            print('{0} {1} {2}'.format(game.game_id + (' ' * (gid_len - len(game.game_id))),x, game.name))
            
        return
    elif cmd == 'show':
        game_list = db.list_games()
                
        gid_len = 0
        for gid,name in game_list:
            length = len(gid)
            if length > gid_len:
                gid_len = length
                
        for gid,name in game_list:
            print('{} {}'.format(gid + (' ' * (gid_len - len(gid))),name))
    elif cmd == 'add':
        if not args:
            done = False
            while not done:
                game = games.Game('game','A Game','','','')
                games.add_game(db,game,ask=True)
                valid_input = False
                while not valid_input:
                    x = input('Add another game? [Y/n] ')
                    if x.lower() == 'y' or x.lower() == 'yes':
                        valid_input = True
                        done = False
                        break
                    elif x.lower() == 'n' or x.lower() == 'no':
                        valid_input = True
                        done = True
                        break
                    else:
                        valid_input = False
        else:
            for i in args:
                game = games.parse_gameconf(i)
                if not game:
                    game = games.Game(i,i,'','','')
                if game.name:
                    print('Adding game "{}".'.format(game.name))
                else:
                    print('Adding game with ID "{}".'.format(game.game_id))
                games.add_game(db,game,ask=True)
    elif cmd == 'remove':
        if not args:
            print("No GameIDs given!",file=sys.stderr)
            return 2
        
        game_list = []
        for gid in args:
            game = db.get_game(gid)
            if not game:
                print ('GameID "{0}" not in database!'.format(gid),file=sys.stderr)
                return 2
            game_list.append(game)
            
        for game in games:
            games.remove_game(db,game,force)
    
    return 0
# command_game()

def command_plugin(db,argv):
    if not argv:
        print('[sgbackup plugin] No command given!',file=sys.stderr)
        help.print_help('plugin')
        return 2
        
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
            
            if plugin.enabled:
                enabled = "* "
            else:
                enabled = "  "
            
            if (len(i) < length):
                s= enabled + i + " " * (length - len(i)) + plugin.description
            else:
                s = enabled + i + " " + plugin.description
                
            print(s)
    elif cmd == 'enable':
        if len(argv) < 2:
            print("[spbackup plugin enable] ERROR: No Plugins given!",file=sys.stderr)
            help.print_help('plugin')
        for i in argv[1:]:
            if i not in plugins.PLUGINS:
                print('No plugin "{0} found!"'.format(i),file=sys.stderr)
                                
        for i in argv[1:]:
            db.enable_plugin(i)
    elif cmd == 'disable':
        if len(argv) < 2:
            print("[spbackup plugin disable] ERROR: No Plugins given!",file=sys.stderr)
            help.print_help('plugin')
        for i in argv[1:]:
            db.disable_plugin(i)
    elif cmd == 'update':
        db_plugins = db.list_plugins()
        
        for i,plugin in plugins.PLUGINS.items():
            p = None
            for j in db_plugins:
                if j['name'] == i:
                    p = j
            if not p:
                if config.CONFIG['verbose']:
                    print('[plugin add] {0}'.format(i))
                db.add_plugin(i)
            elif not plugin.check_version(p['version']):
                if config.CONFIG['verbose']:
                    print("[plugin update] {0}: {1}->{2}".format(i,p['version'],plugin.version))
                plugin.update(db)
    else:
        print('[sgbackup plugin] No such command "{0}"!'.format(cmd),file=sys.stderr)
        help.print_help('plugin')
        
    return 0
# command_plugin
        
    
def command_restore(db,argv):
    try:
        opts,args = getopt.getopt(argv,'cVv',['choose','no-verbose','verbose'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        help.print_help('restore')
        return 2
    
    if not args:
        print("[sgbackup restore] No GameIDs given!",file=sys.stderr)
        help.print_help('restore')
        return 2
    
    for game_id in args:
        if not db.has_game(game_id):
            print("[sgbackup restore] No game for GameID '{0}' found!".format(game_id))
            return 2
                
    choose = False
    for o,a in opts:
        if o == '-c' or o == '--choose':
            choose = True
        elif o == '-V' or o == 'no-verbose':
            config.CONFIG['verbose'] = False
        elif o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
            
    for game_id in args:
        game = db.get_game(game_id)
        latest_backup = backup.find_latest_backup(game)
        if not latest_backup:
            print("[sgbackup restore] No SaveGame for \"{0}\" found!".format(game.name))
            continue
            
        if choose:
            backup.restore_ask(db,game)
        else:
            print("[sgbackup restore] {0}".format(game.name))
            backup.restore(db,game,latest_backup)
            
    return 0
# command_restore()

def command_restore_all(db,argv):
    try:
        opts,args = getopt.getopt(argv,'v', ['--verbose'])
    except getopt.GetoptError as error:
        print(error, file=sys.stderr)
        print(COMMANDS['restore-all']['help-function']('restore-all'))
        return 2
        
    if args:
        print("[sgbackup restore-all] Command does not take any arguments!",file=sys.stderr)
        help.print_help('restore-all')
        return 2
        
    for o,a in opts:
        if o == '-v' or o == '--verbose':
            config.CONFIG['verbose'] = True
    
    backup.restore_all(db)
    
    return 0
# command_restore_all()

def command_version(db,argv):
    print("sgbackup {0}".format('.'.join((str(i) for i in config.CONFIG['version']))))
    return 0
# command_version

def command_write_config(db,argv):
    try:
        opts,args = getopt.getopt(argv, 'gv', ['global','verbose'])
    except GetoptError as error:
        print(error,file=sys.stderr)
        help.print_help('write-config')
        return 2
            
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
            return 3
    else:
        for i in args:
            if config.CONFIG['verbose']:
                print('[sgbackup write-config] {0}'.format(i))
            try: 
                config.write_config(i,global_config)
            except Exception as error:
                print('Writing Config \'{0}\' failed! ({1})'.format(i,error),file=sys.stderr)
                return 3
    return 0
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
    'extension': {
        'description': 'Show filename extensions.',
        'help-function': _get_command_help,
        'function': command_extension
    },
    'game': {
        'description': 'Show/Add/Remove games.',
        'help-function': _get_command_help,
        'function': command_game
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

