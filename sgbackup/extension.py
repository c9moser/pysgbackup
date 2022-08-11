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

from .config import CONFIG

_archiver_extensions=lambda s: sorted(CONFIG['archivers'].keys())

EXTENSIONS={
    'archiver': {
        'description': 'Filename extensions for archivers.',
        'function': _archiver_extensions
    }
}

def get_extensions_names():
    return sorted(EXTENSIONS.keys())
    

def get_extensions(name):
    if not name in EXTENSIONS:
        raise LookupError('Extensions name "{0}" not found!'.format(name))
        
    ext = EXTENSIONS[name]
    if 'function' in ext:
        return ext['function'](name)
    elif 'extensions' in ext:
        return sorted(ext['extensions'])
    else:
        raise LookupError('No extension for name "{0}" found!'.format(name))

