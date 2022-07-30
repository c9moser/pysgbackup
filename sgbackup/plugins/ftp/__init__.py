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

from sgbackup import plugins

class FtpPlugin(plugins.Plugin):
    def __init__(self):
        plugins.Plugin.__init__(self,'ftp')

    def command_ftp(self,db,argv):
        pass

