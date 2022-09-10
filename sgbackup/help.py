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

import sys
from . import commands,config
import pydoc

def print_help(command=None):
    help='No help for command "{0}" available!'.format(command)
    if not command:
        help=commands._get_help()
    elif command not in commands.COMMANDS:
        print('Unknown command "{0}"!'.format(command),file=sys.stderr)
        help=commands._get_help()   
    elif 'help-function' in commands.COMMANDS[command]:
        help=commands.COMMANDS[command]['help-function'](command)
    elif 'help' in commands.COMMANDS[command]:
        help=commands.COMMANDS[command]['help']
        
    if sys.stdout.isatty():
        pydoc.pager(help)
    else:
        print(help)

