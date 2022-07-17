#!/usr/bin/env python
#-*- coding:utf-8 -*-

from . import config,backup,database,archivers

import sys
import getopt

HELP="""sgbackup: Help

USAGE:
======
  sgbackup [help] | [help command]
  sgbackup command [options] [args] ...
  
COMMANDS:
=========
  archiver          list known archivers
  backup            backup savegames
  config            set/get configuration values
  database          database operations (same as db)
  db                database operations (same as database)
  delete-savegame   delete savegames
  delete-backups    delete savegame backups
  help [command]    print help [for command]
  restore           restore savegame backup
  restore-all       restore all savegame-backups
  write-config      write a full configuration file
"""

COMMAND_ARCHIVER_HELP="""sgbackup archivers: Help

USAGE:
======
  sgbackup archiver

DESCRIPTION:
============

This command takes no arguments. It only lists known archivers.  
"""

def command_archiver(db,argv):
    if not argv:
        for i in archivers.list_archivers():
            print(i)
    else:
        print('sgbackup archiver: This command takes no arguments!')
        print(COMMAND_ARCHIVER_HELP)
        sys.exit(2)
    

COMMAND_BACKUP_HELP="""sgbackup backup: Help

USAGE:
======
  sgbackup backup [otions] GameID ...
  
OPTIONS:
========
  -F | --no-final           Create a normal backup and remove final_backup flag
                            if set.
  -f | --final              Create a final backup and set final_backup flag.
  -L file | --listfile=file Set listfile to filename.
  -v | -- verbose           Verbose output.
  -W | --no-write-listfile  Don't write a listfile.
  -w | --write-listfile     Write a listfile.
"""

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
        print(COMMAND_BACKUP_HELP)
        sys.exit(2)
    
    final_backup = False
    remove_final_backup_flag = False
    for o,a in opts:
        if (o == '-F' or o == '..no-final'):
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
        print(COMMAND_BACKUP_HELP)
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

COMMAND_BACKUP_ALL_HELP="""sgbackup backup-all: Help

USAGE:
======
  sgbackup backup-all [options]
  
OPTIONS:
========
  -f | --force              Force all games including finished ones to 
                            be backed up.
  -L file | --listfile=file Write to listfile $file.
  -W | --no-write-listfile  Don't write a listfile.
  -w | --write-listfile     Write listfile.
  -v | --verbose            Verbose output.
"""

def command_backup_all(db,argv):
    try:
        opts,args = getopt.getopt(argv,'fL:vWw',
                                  ['force',
                                   'listfile=',
                                   'no-write_listfile'
                                   'verbose',
                                   'write-listfile'])
    except getopt.GetoptError as error:
        print(error,file=sys.stderr)
        print(COMMAND_BACKUP_ALL_HELP)
        sys.exit(2)
    
    if args:
        print('sgbackup backup-all takes no arguments!',file=sys.stderr)
        print(COMMAND_BACKUP_ALL_HELP)
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

COMMAND_DATABASE_HELP="""sgbackup database: Help

USAGE:
======
  sgbackup database <COMMAND> [OPTIONS] [ARGS] ...
  
  sgbackup database <list | list-ids | list-names>
  sgbackup database <name | delete | show> <GameID> ...
  sgbackup database [-f] [-v] update [GameID] ...
  
COMMANDS:
=========
  delete        Deletes a game from database.
  list          List games in database.
  list-ids      List game ids only.
  list-names    List game names only.
  name          Get name of the game by GameID.
  show          Show Game config for GameIDs
  update        Updates the database from ${GameID}.conf files.

OPTIONS:
========
  -f | --force      Force database operation.
  -v | --verbose    Enable verbose output.
"""

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
        print(COMMAND_DATABASE_HELP)
    if (argv[0]) not in commands:
        print("sgbackup database: Unknown command '{0}'!".format(argv[0]),file=sys.stderr)
        print(COMMAND_DATABASE_HELP)
    
    try:   
        opts,args = getopt.getopt(argv[1:], 'fv', ['force','verbose'])
    except getopt.GetoptError as err:
        print(err,file=sys.stderr)
        print(COMMAND_DATABASE_HELP)
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
            print(COMMAND_DATABASE_HELP)
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
            print(COMMAND_DATABASE_HELP)
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
            print(COMMAND_DATABASE_HELP)
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
 
COMMAND_WRITE_CONFIG_HELP="""sgbackup write-config: Help

USAGE:
======
  sgbackup write-config [options] [filename] ...
  
OPTIONS:
========
  -g | --global     Write a global file
  -v | --verbose    Verbose output
"""
   
def command_write_config(db,argv):
    try:
        opts,args = getopt.getopt(argv, 'gv', ['global','verbose'])
    except GetoptError as error:
        print(error,file=sys.stderr)
        print(COMMAND_WRITE_CONFIG_HELP)
            
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
            filename = os.path.normpath(config.CONFIG['user-config'])
            
        if config.CONFIG['verbose']:
            print('[sgbackup write-config] {0}'.format(filename))
        try:
            config.write_config(filename,global_config)
        except Exception as error:
            print('Writing Config \'{0}\' failed! ({1})'.format(i,error),file=sys.stderr)          
    else:
        for i in args:
            if config.CONFIG['verbose']:
                print('[sgbackup write-config] {0}'.format(i))
            try: 
                config.write_config(i,global_config)
            except Exception as error:
                print('Writing Config \'{0}\' failed! ({1})'.format(i,error),file=sys.stderr)
# command_write_config()

COMMAND_NOT_IMPLEMENTED_HELP="""COMMAND IS NOT IMPLEMENTED!

This is work in progress!
"""
command_not_implemented = lambda db,argv: print('Not Implemented!')

commands={
    'archiver': {'help':COMMAND_ARCHIVER_HELP,'function':command_archiver},
    'config': {'help':COMMAND_NOT_IMPLEMENTED_HELP,'function':command_not_implemented},
    'backup': {'help': COMMAND_BACKUP_HELP,'function':command_backup},
    'backup-all': {'help': COMMAND_BACKUP_ALL_HELP,'function':command_backup_all},
    'database': {'help':COMMAND_DATABASE_HELP,'function':command_database},
    'db': {'help':COMMAND_DATABASE_HELP,'function':command_database},
    'delete-backups': {'help': COMMAND_NOT_IMPLEMENTED_HELP, 'function': command_not_implemented},
    'delete-savegames': {'help': COMMAND_NOT_IMPLEMENTED_HELP, 'function': command_not_implemented},
    'restore': {'help': COMMAND_NOT_IMPLEMENTED_HELP, 'function': command_not_implemented},
    'restore-all': {'help':COMMAND_NOT_IMPLEMENTED_HELP,'function': command_not_implemented},
    'write-config': {'help': COMMAND_WRITE_CONFIG_HELP,'function': command_write_config}
}
    
def main():
    if len(sys.argv) == 1:
        print(HELP)
        sys.exit(0)
    if sys.argv[1] == "help":
        if len(sys.argv) == 2:
            print(HELP)
            sys.exit(0)
        if sys.argv[2] not in commands.keys():
            print("No help for '{0}' found!".format(sys.argv[2]),file=sys.stderr)
            print(HELP)
            sys.exit(2)
        print(commands[sys.argv[2]]['help'])
        sys.exit(0)
    elif sys.argv[1] in commands.keys():
        db = database.Database()
        
        commands[sys.argv[1]]['function'](db,sys.argv[2:])
    else:
        print("sgbackup: Unknown command '{0}'!".format(sys.argv[1]),file=sys.stderr)
        print(HELP)
        sys.exit(2)
# main()

if __name__ == "__main__":
    main()


