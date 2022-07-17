#-*- coding:utf-8 -*-

import gi
from gi.repository import GLib
import os
import sys
import configparser
from string import Template
import hashlib
import zipfile

def _get_cehcksum_values():
    def get_checksum(filename,algorithm='None'):
        if algorithm == 'None':
            return ''
            
        with open(filename,'rb') as f:
            h = hashlib.new(algorithm)
            h.update(f.read())
            return h.hexdigest()
    # get_checksum()
    
    values = {'None': lambda f: get_checksum(f)}
    
    for i in hashlib.algorithms_available:
        values[i] = lambda f: get_checksum(f,i)
        
    return values
        
    
CONFIG={
    "version":(0,0,2),
    "global-config": os.path.join(os.path.dirname(__file__),"sgbackup.conf"),
    "user-name": GLib.get_user_name(),
    "user-data-dir": os.path.join(GLib.get_user_data_dir(),"sgbackup"),
    "user-config": os.path.join(GLib.get_user_data_dir(),"sgbackup","sgbackup.conf"),
    "database.create-sql": os.path.join(os.path.dirname(__file__),"sqlite3.db.sql"),
    
    # Variables changed by config files
    "verbose": False,
    "database": os.path.join(GLib.get_user_data_dir(),"sgbackup", "sgbackup.db"),
    "user-archivers-dir": os.path.join(GLib.get_user_data_dir(),"sgbackup","archivers"),
    "user-gameconf-dir": os.path.join(GLib.get_user_data_dir(),"sgbackup","games"),
    
    "backup.max": 10,
    "backup.checksum": "sha256",
    "backup.checksum.values": _get_cehcksum_values(),
    "backup.archiver": "zipfile",
    "backup.dir": os.path.join(GLib.get_home_dir(), "SaveGames"),
    "backup.write-listfile": False,
    "backup.archiver": "zipfile",
    
    "zipfile.compression": zipfile.ZIP_DEFLATED,
    "zipfile.compresslevel": 9,
    "zipfile.compression.values": {
        'stored': zipfile.ZIP_STORED,
        'deflated': zipfile.ZIP_DEFLATED,
        'bzip2': zipfile.ZIP_BZIP2,
        'lzma': zipfile.ZIP_LZMA
    },
    
    # Variables for game.conf files and database entries
    "template-variables": {
        "USER_HOME": GLib.get_home_dir(),
        "USER_DATA_DIR": GLib.get_user_data_dir(),
        "USER_DOCUMENTS_DIR": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS),
        "USER_NAME": GLib.get_user_name()
    }
    
}
CONFIG['backup.listfile']=os.path.join(CONFIG['backup.dir'],"backups.list")

CONFIG_DIRS=[
    "user-data-dir",
    "user-archivers-dir",
    "user-gameconf-dir"
]

def _init_config():
    def parse_config(cparser):
        if cparser.has_section("variables"):
            for opt in cparser.options("vaiables"):
                CONFIG["template-variables"][opt]=cparser.get_option("variables",opt)
        v=dict(os.environ)
        v.update(CONFIG["template-variables"])
        v.update({'BACKUP_DIR': CONFIG['backup.dir']})
     
        sect="config"
        if cparser.has_section(sect):
            if cparser.has_option(sect,"verbose"):
                CONFIG['verbose'] = cparser.getboolean(sect,'verbose')
            if cparser.has_option(sect,'user-config'):
                CONFIG['user-config-template']=cparser.get(sect,'user-config')
                t=Template(cparser.get(sect,'user-config'))
                CONFIG['user-config']=os.path.normpath(t.substitute(v))
            if cparser.has_option(sect,'user-achivers-dir'):
                CONFIG['user-archivers-dir-template']=cparser.get(sect,"user-archivers-dir")
                t=Template(cparser.get(sect,"user-archivers-dir"))
                CONFIG["user-achivers-dir"] = os,path.normpath(t.substitute(v))
            if cparser.has_option(sect,"user-db"):
                CONFIG["database-template"]=cparser.get(sect,"database")
                t=Template(cparser.get(sect,"database"))
                CONFIG["database"] = os.path.normpath(t.substitute(v))
            if cparser.has_option(sect,"user-gameconf-dir"):
                CONFIG["user-gameconf-dir-template"]=cparser.get(sect,"user-gameconf-dir")
                t=Template(cparser.get(sect,"user-gameconf-dir"))
                CONFIG["user-gameconf-dir"]=os.path.normpath(t.substitute(v))
        
        sect="backup"
        if (cparser.has_section(sect)):
            if cparser.has_option(sect, "dir"):
                CONFIG['backup.dir.template']=cparser.get_option(sect,"dir")
                t=Template(cparser.get_option(sect,"dir"))
                value = t.substitute(v)
                CONFIG["backup.dir"] = os.path.normpath(value)
                v["BACKUP_DIR"] = value
            if cparser.has_option(sect, "max-backups"):
                CONFIG["backups.max"] = cparser.getint(sect, "max-backups")
            if cparser.has_option(sect, "checksum"):
                x=cparser.get(sect,"checksum")
                if (not x.strip() or x.upper() == "NONE"):
                    CONFIG["backup.checksum"] = None
                elif (x in hashlib.algorithms_available):
                    CONFIG["backup.checksum"] = x
            if cparser.has_option(sect,'listfile'):
                CONFIG['backup.listfile.template']=cparser.get(sect,"listfile")
                t=Template(cparser.get(sect,"listfile"))
                CONFIG['backup.listfile'] = os.path.normpath(t.substitute(v))
            if cparser.has_option(sect,'write-listfile'):
                CONFIG['backup.write-listfile'] = cparser.getboolean(sect,'write-listfile')
                
        sect="zipfile"
        if cparser.has_section(sect):
            if cparser.has_option(sect,'compression'):
                opt = cparser.get(sect,'compression')
                if (not opt or opt not in CONFIG['zipfile.compression.values'].keys()):
                    print("CONFIG WARNING: [zipfile] compression {0} is not known! Using default compression!".format(opt))
                else:
                    CONFIG["zipfile.compression"] = CONFIG['zipfile.compression.values'][opt]
            if cparser.has_option(sect,'compresslevel'):
                CONFIG['zipfile.compresslevel'] = cparser.getint(sect,'compresslevel')
                
    # parse_config()
    
    cfg = configparser.ConfigParser()
    
    if os.path.exists(CONFIG['global-config']):
        cfg.read(CONFIG['global-config'])
        parse_config(cfg)
        
    if os.path.exists(CONFIG['user-config']):
        cf.read(CONFIG['user-config'])
        parse_config(cfg)
# _init_config()

def _init_config_dirs():
    for i in CONFIG_DIRS:
        d = CONFIG[i]
        if not os.path.exists(d):            
            os.makedirs(d)

_init_config()
_init_config_dirs()

def _bool_to_config(b):
    if (b):
        return 'yes'
    return 'no'

def write_config(filename,global_config=False):
    if (global_config):
        config_file=CONFIG['global-config']
    else:
        config_file=CONFIG['user-config']
        
    cparser = configparser.ConfigParser()
    
    sect='config'
    cparser.add_section(sect)
    if global_config:
        if 'user-config-template' in CONFIG.keys():
            cparser.set(sect,'user-config',CONFIG['user-config-template'])
    if 'database-template' in CONFIG.keys():
        cparser.set(sect,'database',CONFIG['database-template'])
    if 'user-gameconf-dir-template' in CONFIG.keys():
        cparser.set(sect,'user-gameconf-dir',CONFIG['user-gameconf-dir-template'])
    if 'user-archivers-dir-template' in CONFIG.keys():
        cparser.set(sect,'user-archivers-dir',CONFIG['user-archivers-dir-template'])
    cparser.set(sect,'verbose',_bool_to_config(CONFIG['verbose']))
    
    sect='backup'
    cparser.add_section(sect)
    cparser.set(sect,'max',str(CONFIG['backup.max']))
    cparser.set(sect,'checksum',CONFIG['backup.checksum'])
    cparser.set(sect,'archiver',CONFIG['backup.archiver'])
    if 'backup.dir.template' in CONFIG.keys():
        cparser.set(sect,'dir',CONFIG['backup.dir.template'])
    if 'backup.listfile.template' in CONFIG.keys():
        cparser.set(sect,'listfile',CONFIG['backup.listfile.template'])
    cparser.set(sect,'write-listfile',_bool_to_config(CONFIG['backup.write-listfile']))

    zf_compress={}
    for k,v in CONFIG['zipfile.compression.values'].items():
        zf_compress[v]=k
        
    sect='zipfile'
    cparser.add_section(sect)
    cparser.set(sect,'compression',zf_compress[CONFIG['zipfile.compression']])
    cparser.set(sect,'compresslevel',str(CONFIG['zipfile.compresslevel']))
    
    with open(filename,'w') as f:
        cparser.write(f)
# write_config()


