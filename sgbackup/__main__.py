#!/usr/bin/env python
#-*- coding:utf-8 -*-

from . import config

import sys

from .commands import COMMANDS
from . import database

def main():
    if len(sys.argv) == 1:
        print(COMMANDS['help']['help-function']('help'))
        sys.exit(0)
    elif sys.argv[1] in COMMANDS:
        db = database.Database()
        COMMANDS[sys.argv[1]]['function'](db,sys.argv[2:])
    else:
        print("sgbackup: Unknown command '{0}'!".format(sys.argv[1]),file=sys.stderr)
        print(COMMANDS['help']['help-function']('help'))
        sys.exit(2)
# main()

if __name__ == "__main__":
    main()


