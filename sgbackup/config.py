#-*- coding:utf-8 -*-

import gi
from gi.repository import GLib
import os
import sys
import configparser
from string import Template
import hashlib
import zipfile

def _get_checksum_values():
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
    "version":(0,0,4),
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
    "backup.checksum.values": _get_checksum_values(),
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
    },
    'archivers': {
        'tar': {'archiver':'tarfile'},
        'zip': {'archiver':'zipfile'}
    }
}
CONFIG['backup.listfile']=os.path.join(CONFIG['backup.dir'],"backups.list")
CONFIG['backup.checksum-database.template']="${BACKUP_DIR}/checksums.db"
CONFIG['backup.checksum-database']=os.path.join(CONFIG['backup.dir'],'checksums.db')

CONFIG_DIRS=[
    "user-data-dir",
    "user-archivers-dir",
    "user-gameconf-dir"
]

def _init_config():
    def parse_config(cparser):
        if cparser.has_section("variables"):
            for opt in cparser.options("variables"):
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
                CONFIG["template-variables"]['BACKUP_DIR'] = value
                v["BACKUP_DIR"] = os.path.normpath(value)
                
                t = Template(CONFIG['backup-checksum-database.template'])
                CONFIG['backup.checksum-database'] = t.substitute(v)
                    
            if cparser.has_option(sect,'archiver'):
                CONFIG['backup.archiver'] = cparser.get(sect,'archiver')
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
            if cparser.has_option(sect,'checksum-database'):
                CONFIG['backup.checksum-database.template'] = cparser.get(sect,'checksum-database')
                t = Template(cparser.get(sect,'checksum-database'))
                CONFIG['backup.checksum-database'] = os.path.normpath(t.substitute(v))
                
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
    
    if os.path.isfile(CONFIG['global-config']):
        cfg.read(CONFIG['global-config'])
        parse_config(cfg)
        
    if os.path.isfile(CONFIG['user-config']):
        cfg.read(CONFIG['user-config'])
        parse_config(cfg)
# _init_config()

def _init_config_dirs():
    for i in CONFIG_DIRS:
        d = CONFIG[i]
        if not os.path.exists(d):            
            os.makedirs(d)

_init_config()
_init_config_dirs()

from . import archivers

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
    if 'backup.checksum-database.template' in CONFIG:
        cparser.set(sect,'checksum-database',CONFIG['backup.checksum-database.template'])
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

def _get_config_fallback(key,fallback):
    if key in CONFIG:
        return CONFIG[key]
    return CONFIG[fallback]
# _get_config_fallback()

def _get_config_dict(global_config=False):
    d={
        'verbose':_bool_to_config(CONFIG['verbose']),
        'database': _get_config_fallback('database-template','database'),
        'backup.max': CONFIG['backup.max'],
        'backup.dir': _get_config_fallback('backup.dir.template','backup.dir'),
        'backup.checksum': CONFIG['backup.checksum'],
        'backup.archiver': CONFIG['backup.archiver'],
        'backup.listfile': _get_config_fallback('backup.listfile.template','backup.listfile'),
        'backup.checksum-database': _get_config_fallback('backup.checksum-database.template','backup.checksum-database'),
        'backup.write-listfile': _bool_to_config(CONFIG['backup.write-listfile']),
        'zipfile.compression': CONFIG['zipfile.compression'],
        'zipfile.compresslevel': CONFIG['zipfile.compresslevel']
    }
    if global_config:
        d.update({
            'user-config': _get_config_fallback('user-config-template','user-config'),
            'user-archivers-dir': _get_config_fallback('user-archivers-dir-template','user-archivers-dir'),
            'user-gameconf-dir': _get_config_fallback('user-gameconf-dir-template','user-gameconf-dir'),
        })
    return d
# _get_config_dict()

def print_config(global_config=False):
    d = _get_config_dict(global_config)
    for i in sorted(d.keys()):
        print('{0}={1}'.format(i,d[i]))
# print_config()
        
def print_config_key(key,global_config=False):
    d = _get_config_dict(global_config)
    
    if key not in d:
        raise LookupError('Key \'{0}\' not in config!'.format(key))

    print('{0}={1}'.format(key,d[key]))
# print_config_key()

def print_config_value(key,global_config=False):
    boolean ="boolean [1|0|y|n|yes|no|true|false]"
    path_template = "path template"
    integer = "integer"
    
    if key == 'verbose':
        value = boolean
    elif key == 'database':
        value = path_template
    elif key == 'user-config':
        value = path_template
    elif key == 'user-archivers-dir':
        value = path_template
    elif key == 'user-gameconf-dir':
        value = path_template
    elif key == 'backup.dir':
        value = path_template
    elif key == 'backup.max':
        value = integer
    elif key == 'backup.archiver':
        value = 'string [{0}]'.format('|'.join(archivers.ARCHIVERS.keys()))
    elif key == 'backup.checksum':
        value = 'string [{0}]'.format('|'.join(CONFIG['backup.checksum.values']))
    elif key == 'backup.checksum-database':
        value = path_template
    elif key == 'backup.listfile':
        value = path_template
    elif key == 'backup.write-listfile':
        value = boolean
    elif key == 'zipfile.compression':
        value = 'string [{0}]'.format(CONFIG['zipfile.compression.values'].keys())
    elif key == 'zipfile.compresslevel':
        if CONFIG['zipfile.compression'] == zifile.ZIP_BZIP2:
            CONFIG[key] = "integer [1-9]"
        else:
            CONFIG[key] = "integer [0-9]"
    else:
        raise LookupError("Key '{0}' not in config!".format(key))
        
    print("{0}: {1}".format(key,value))
# print_config_value()
    
def write_config_key(key,value,global_config=False):
    def _min_value(value,minimum):
        if (value < minimum):
            return minimum
        return value
        
    def _max_value(value,maximum):
        if (value > maximum):
            return maximum
        return value
        
    _min_max = lambda v,_min,_max: _max_value(_min_value(v,_min),_max)
    
    def _arg_to_bool(arg):
        if (arg == "1" or arg.lower() == 'y' or arg.lower() == 'yes' or arg.lower() == 'true'):
            return True
        elif (arg == '0' or arg.lower() == 'n' or arg.lower() == 'no' or arg.lower() == 'false'):
            return False

        raise ValueError("Unable to convert '{0}' to bool!")
    # _arg_to_bool
    
    v=dict(os.environ)
    v.update(CONFIG['template-variables'])
    v.update({'BACKUP_DIR': CONFIG['backup.dir']})

    # set config    
    if key == 'verbose':
        CONFIG['verbose']=_arg_to_bool(value)
    elif key == 'database':
        CONFIG['database-template'] = value
        t = Template(value)
        CONFIG[key] = t.substitute(v)
    elif key == 'user-config':
        CONFIG['user-config-template'] = value
        t = Template(value)
        CONFIG[key] = t.substitute(v)
    elif key == 'user-archivers-dir':
        CONFIG['user-archivers-dir-template'] = v
        t = Template(value)
        CONFIG[key] = t.substitute(v)
    elif key == 'user-gameconf-dir':
        CONFIG['user-gameconf-dir-template'] = value
        t = Template(value)
        CONFIG[key] = t.substitute(v)
    elif key == 'backup.dir':
        CONFIG['backup.dir.template'] = value
        t = Template(value)
        CONFIG['backup.dir'] = t.substitute(v)
        v['BACKUP_DIR'] = t.substitute(v)
    elif key == 'backup.max':
        CONFIG[key] = int(value)
    elif key == 'backup.archiver':
        if value in archivers.ARCHIVERS:
            CONFIG[key] = value
        else:
            raise ValueError('{0} needs to be a valid ArchiverID!'.format(key))
    elif key == 'backup.checksum':
        if value in CONFIG['backup.checksum.values']:
            CONFIG[key] = value
        else:
            raise ValueError('{0} needs to be a valid checksum algorithm!'.format(key))
    elif key == 'backup.checksum-database':
        CONFIG['backup.checksum-database.template'] = value
        t = Template(value)
        CONFIG['backup.checksum-database'] = t.substitute(v)
    elif key == 'backup.listfile':
        CONFIG['backup.listfile.template'] = value
        t = Template(value)
        CONFIG[key] = t.substitute(v)
    elif key == 'backup.write-listfile':
        CONFIG[key] = _bool_to_config(value)
    elif key == 'zipfile.compression':
        if value in CONFIG['zipfile.compression.values']:
            CONFIG[key] = CONFIG['zipfile.compression.values'][value]
        else:
            raise ValueError('{0} needs to be a valid zipfile compression!'.format(key))
    elif key == 'zipfile.compresslevel':
        if CONFIG['zipfile.compression'] == zifile.ZIP_BZIP2:
            CONFIG[key] = _min_max(int(value),1,9)
        else:
            CONFIG[key] = _min_max(int(value),0,9)
    else:
        raise LookupError('Key \'{0}\' not in config!'.format(key))
    
    if global_config:
        filename=CONFIG['global-config']
    else:
        filename=CONFIG['user-config']
        
    write_config(filename,global_config)
# write_config_key()

