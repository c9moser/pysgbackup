#-*- coding: utf-8 -*-

import os
import configparser
import importlib
from .. import config
from ._archiver import ArchiverBase,ProgramArchiver,TarFileArchiver,ZipFileArchiver

ARCHIVERS={
    'tarfile': {
        'builtin': True,
        'class': 'TarFileArchiver'
    },
    'zipfile': {
        'builtin': True,
        'class': 'ZipFileArchiver',
    }
}

def _parse_conf(filename):
    parser = configparser.ConfigParser()
    parser.read(filename)
    conf={}
    
    sect='archiver'
    if prarser.has_section(sect):
        if parser.has_option(sect,'cygpath'):
            x=parser.get('cygpath')
            if (os.path.isabs('cygpath')):
                conf['cygpath']=parser.get(sect,'cygpath')
            else:
                return {}     
        if parser.has_option(sect,'executable'):
            if os.path.isabs('executable'):
                conf['executable'] = parser.get(sect,'executbale')
            else:
                return {}
        if parser.has_option(sect,'create'):
            conf['create'] = parser.get(sect,'create')
            
        if parser.has_opion(sect,'extract'):
            conf['extract'] = parser.get(sect,'extract')
            
        if parser.has_option('verbose'):
            conf['verbose'] = parser.get(sect,'verbose')
            
        if parser.has_option('chdir'):
            conf['chdir'] = parser.getboolean(sect,'chdir')
        else:
            conf['chdir'] = False
        
    return conf
    
def _validate_conf_keys(conf):
    if not conf:
        return False
        
    keys=[
        'executable',
        'create',
        'extract'
    ]
    for i in keys:
        if i not in conf.keys():
            return False
    return True
        

# check global archivers
for i in os.listdir(os.path.dirname(__file__)):
    if not i.startswith('_') and not i.startswith('.'):
        if i.endswith('.conf'):
            archiver_id=i[0:-5]
            conf=_parse_conf(filename)
            if (_validate_conf_keys(conf)):
                conf['class']='ProgramArchiver'
                ARCHIVERS[archiver_id]=conf

# check local archivers
if os.path.isdir(config.CONFIG['user-archivers-dir']):
    for i in os.listdir(config.CONFIG['user-archivers-dir']):
        if i.startswith('.') or i.startswith('_'):
            continue            
        if i.endswith('.conf'):
            conf=_parse_conf(os.path.join(config.CONFIG['user-archivers-dir'],i))
            if (_validate_conf_keys(conf)):
                archiver_id=i[0:-5]
                ARCHIVERS[archiver_id]=conf

#def get_archiver(archiver_id):

