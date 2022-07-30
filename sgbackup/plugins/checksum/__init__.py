#-*- coding:utf-8 -*-
################################################################################
# sgbackup - cksum
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
import os
import subprocess
import gettext
from sgbackup.config import CONFIG

N_ = lambda s: (s)
def Q_(msgid):
    s = gettext.gettext(msgid)
    if msgid == s:
        if  '|' in msgid:
            return msgid.split('|',1)
    return s

if sys.platform == 'win32':
    def _get_checksum_programs():
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
        usr_bin = os.path.join(root_dir,'usr','bin')
        cygpath = ""

        ret = {}
        cksum_exe = ['b2sum.exe',
                     'md5sum.exe',
                     'sha1sum.exe',
                     'sha224sum.exe',
                     'sha256sum.exe',
                     'sha384sum.exe',
                     'sha512sum.exe']
        
        if os.path.isdir(usr_bin):
            if os.path.isfile(os.path.join(usr_bin,'cygpath.exe')):
                cygpath=os.path.join(usr_bin,'cygpath.exe')
            for i in cksum_exe:
                exe = os.path.join(usr_bin,i)
                if os.path.isfile(exe):
                    ret[i[:-7]]=exe
        
        return ret
    # _get_checksum_programs()
        
else:
    def _get_checksum_programs():
        ret = {}
        cksum_exe = ['b2sum',
                     'md5sum',
                     'sha1sum',
                     'sha224sum',
                     'sha256sum',
                     'sha384sum',
                     'sha512sum']

        path = os.environ['PATH'].split(':')
        for i in cksum_exe:
            for j in path:
                if os.path.isfile(os.path.join(j,i)):
                    ret[i[:-3]] = os.path.join(j,i)
                    break
                    
        return ret
    # _get_checksum_programs()
    
CHECKSUM = _get_checksum_programs()

_HELP={
    'checksum': N_('file|command.checksum.help.txt'),
    'checksum-all': N_('file|command.checksum.all.txt')
}    

def _get_help(cmd):
    filename = os.path.join(os.path.dirname(__file__),Q_(_HELP[cmd]))
    with open(filename,'r') as ifile:
        return ifile.read()

def backup_callback(game,filename):
    if not CONFIG['checksum.enable'] or CONFIG['checksum.algorithm'] == 'None':
        return True
        
    cksum = CONFIG['checksum.algorithm']
    if cksum not in CHECKSUM:
        raise RuntimeError('<checksum> Checksum "{0}" not available!'.format(cksum),file=sys.stderr)
        return False
        
    f = os.path.basename(filename)
    cwd = os.getcwd()
    os.chdir(os.path.dirname(filename))
    
    if CONFIG['checksum.bsd-tags']:
        cmd = '"{0}" --tag "{1}"'.format(CHECKSUM[cksum],f)
    else:
        cmd = '"{0}" "{1}"'.format(CHECKSUM[cksum],f)
        
    proc = subprocess.run(cmd,capture_output=True)
    if proc.returncode != 0:
        return False
        
    with open('.'.join((f,cksum)),'w') as ofile:
        s = str(proc.stdout)
        ofile.write(s[2:-3] + '\n')
        
    if CONFIG['backup.write-listfile']:
        with open(CONFIG['backup.listfile'],'a') as ofile:
            ofile.write('{0}/{1}\n'.format(game.savegame_name,'.'.join((f,cksum))))
    
    os.chdir(cwd)
    return True

def delete_backup_callback(game,filename):
    for cksum in CHECKSUM.keys():
        ckfile = '.'.join((filename,cksum))
        if os.path.isfile(ckfile):
            os.unlink(ckfile)
# delete_backup
    
def command_checksum(db,argv):
    pass
    
def command_checksum_all(db,argv):
    pass
    
if CHECKSUM:
    plugin={
        'name': 'checksum',
        'description': 'Create/Check checksum files.',
        'backup-callback': backup_callback,
        'delete-backup-callback': delete_backup_callback,
        'version': '.'.join((str(i) for i in CONFIG['version'])),
        'config' : {
            'section': 'checksum',
            'global': True,
            'local': True,
            'values': {
                'checksum.enable': {
                    'option': 'enable',
                    'type': 'boolean',
                    'default': False
                },
                'checksum.algorithm': {
                    'type': 'string',
                    'option': 'algorithm',
                    'values': ['None'] + list(CHECKSUM.keys()),
                    'default': 'None'
                },
                'checksum.bsd-tags': {
                    'option': 'bsd-tags',
                    'type': 'boolean',
                    'default': False
                }
            }
        },
        'commands': {
            'checksum': {
                'description': 'Check checksum files against backups for given game.',
                'function': command_checksum,
                'help-function': _get_help
            },
            'checksum-all': {
                'description': 'Check checksum files against backups for all games.',
                'function': command_checksum_all,
                'help-function': _get_help
            }
        }
    }

