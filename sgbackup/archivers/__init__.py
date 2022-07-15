#-*- coding: utf-8 -*-

import os
import configparser
import importlib
from .. import config
from ._archiver import ArchiverBase,ProgramArchiver,TarFileArchiver,ZipFileArchiver

for i in os.listdir(os.path.dirname(__file__)):
    if not i.startswith('_') and not i.startswith('.') and i.endswith('.py'):
        exec("import .{0}".format(i))

def get_archiver(archiver_id):
    global_conf = os.path.join(os.path.dirname(__file__),'.'.join((archiver_id,'conf')))
    user_conf = os.path.join(config.CONFIG['sg-user-archivers-dir'],'.'.join((archiver_id,'conf')))
            
    if not os.path.isfile(global_conf) and not os.path.isfile(user_conf):
        return None
        
    parser = configparser.ConfigParser()
    if os.path.isfile(global_conf):
        parser.read(global_conf)
    if os.path.isfile(user_conf):
        parser.read(user_conf)
        
    archiver=None
    if (has_section('archiver')):
        pass
    return archiver

def list_archivers():
    ret = []
    for i in os.listdir(os.path.dirname(__file__)):
        if i.endswith('.conf'):
            ret.append(i[0:-5])
            
    for i in os.listdir(config.CONFIG['sg-user-archivers-dir']):
        if i.endswith('.conf'):
            aid = i[0:-5]
            if aid not in ret:
                ret.append(aid)
                
    ret = sorted(ret)
    return ret

