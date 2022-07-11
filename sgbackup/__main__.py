#!/usr/bin/env python
#-*- coding:utf-8 -*-

import config
import sys
import getopt

_HELP="""USAGE:\n======
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

_HELP_BACKUP="""
"""

def _backup(argv):
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
    
    mode='c'
    
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


_HELP_DATABASE="""
"""

def _database(argv):
    pass
    
def main():
    if len(sys.argv) == 1:
        print(_HELP)
        sys.exit(0)
    if sys.argv[1] == "help":
        if len(sys.argv) == 2:
            print(_HELP)
            sys.exit(0)
        if sys.argv[2] not in _help_topics.keys():
            print("No help for '{0}' found!".format(sys.argv[2]),file=sys.stderr)
            print(_HELP)
            sys.exit(2)
        print(_help_topics[sys.argv[2]])
        sys.exit(0)
    elif sys.argv[1] == "backup":
        _backup(sys.argv[2:])
    elif sys.argv[1] == "db":
        _database(sys.argv[2:])
        
    
_help_topics={
    'backup': _HELP_BACKUP
    'database': _HELP_DATABASE
    'db': _HELP_DATABASE
}
        
    
if __name__ == "__main__":
    main()


