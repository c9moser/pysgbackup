#!/usr/bin/env python
#-*- coding:utf-8 -*-

from . import config,backup,database

import sys
import getopt

HELP="""USAGE:\n======
  sgbackup [help] | [help command]
  sgbackup command [options] [args] ...
  
COMMANDS:
=========
  help          print help
  help command  print help for specified command
  backup        backup operations
  database      database operations (same as db)
  db            database operations (same as database)
"""

COMMAND_BACKUP_HELP="""
"""

def command_backup(db,argv):
    try:
        opts,args = getopt.getopt(argv, 
                                  "L:ahuw",
                                  ["backup-all",
                                   "help",
                                   "listfile="
                                   "usage"
                                   "write-listfile"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
    
    rtopts={
        "verbose":False,
        "backup-all":False,
        "write-listfile":False,
    }
    
    mode='b'
    
    for o,a in opts:
        if (o == '-L' or o == '--listfile'):
            rtopts['write-listfile']=True
            config.CONFIG['sg-listfile']=a
        elif (o == '-a' or o == '--backup-all'):
            mode='a'
        elif (o == '-h' or o == '--help'):
            print(get_help())
            sys.exit(0)
        elif (o == '-u' or o == '--usage'):
            print(get_usage())
            sys.exit(0)
        elif (o == '-w' or o == '--write-listfile'):
            rtopts['write-listfile']=True
            
    if mode == 'a':
        backup_all_targets


COMMAND_DATABASE_HELP="""sgbackup database: Help

USAGE:
======
  sgbackup database <COMMAND> [OPTIONS] [ARGS] ...
  
  sgbackup database <list | list-ids | list-names>
  sgbackup database <name | delete> <GameID> ...
  sgbackup database [-f] [-v] update [GameID] ...
  
COMMANDS:
=========
  delete        Deletes a game from database.
  list          List games in database.
  list-ids      List game ids only.
  list-names    List game names only.
  name          Get name of the game by GameID.
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
        'update']
    
    if not argv:
        print("sgbackup database: No command given!", file=sys.stderr)
        print(_HELP_DATABASE)
    if (argv[0]) not in commands:
        print("sgbackup database: Unknown command '{0}'!".format(argv[0]),file=sys.stderr)
        print(_HELP_DATABASE)
    
    try:    
        opts,args = getopt.getopt(argv[1:], 'fv', ['force','verbose'])
    except getopt.GetoptError as err:
        print(err,file=sys.stderr)
        print(_HELP_DATABASE)
        sys.exit(2)
   
    force=False
    for opt in opts:
        if opt == '-f' or opt == '--force':
            force = True
        elif opt == '-v' or opt == '--verbose':
            config.CONFIG['verbose'] = True
    
    cmd = argv[0]
    if cmd == 'delete':
        if not args:
            print("sgbackup database delete: No arguments given!'",file=sys.stderr)
            print(_HELP_DATABASE)
            sys.exit(2)
        
        for i in args:
            if not db.has_game(i):
                print("No Game found for GameID '{0}'!",file=sys.stderr)
                sys.exit(2)
                
        for i in args:
            db.delete_game(i)            
    elif cmd == 'list':
        pass
    elif cmd == 'list-ids':
        pass
    elif cmd == 'list-names':
        pass
    elif cmd == 'name':
        pass
    elif cmd == 'update':
        pass
# _database()
    
        

commands={
    'backup': {'help':COMMAND_BACKUP_HELP,'function':command_backup},
    'database': {'help':COMMAND_DATABASE_HELP,'function':command_database},
    'db': {'help':COMMAND_DATABASE_HELP,'function':command_database}
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
        sys.exit(2)
    
if __name__ == "__main__":
    main()


