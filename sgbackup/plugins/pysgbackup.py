#-*- coding:utf-8 -*-
################################################################################
# sgbackup.plugins.pysgbackup
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

"""
This Plugin just adds pysgbackup config variables to sgbackup.config.CONFIG
"""

plugin = {
    'name':'pysgbackup',
    'description': 'Dummy Plugin to add pysgbackup config variables.',
    'config': {
        'global': True,
        'local': True,
        'section': 'pysgbackup',
        'values': {
            'pysgbackup.gameview.show-id': {
                'option': 'gameview.show-id',
                'type': 'boolean',
                'default': True
            },
            'pysgbackup.gameview.show-gameid': {
                'option': 'gameview.show-game-id',
                'type': 'boolean',
                'default': True
            },
            'pysgbackup.gameview.show-final': {
                'option': 'gameview.show-final',
                'type': 'boolean',
                'default': True
            },
            'pysgbackup.gameview.show-steam-appid': {
                'option': 'gameview.show-steam-appid',
                'default': False,
                'type': 'boolean'
            }
        }
    }
}
