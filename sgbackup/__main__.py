#!/usr/bin/env python
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


from . import config

import sys

from .commands import COMMANDS
from . import database

import sgbackup

def main():
    if len(sys.argv) == 1:
        print(COMMANDS['help']['help-function']('help'))
        sys.exit(0)
    elif sys.argv[1] in COMMANDS:
        db = sgbackup.db
        COMMANDS[sys.argv[1]]['function'](db,sys.argv[2:])
    else:
        print("sgbackup: Unknown command '{0}'!".format(sys.argv[1]),file=sys.stderr)
        print(COMMANDS['help']['help-function']('help'))
        sys.exit(2)
# main()

if __name__ == "__main__":
    main()


