#-*- coding:utf-8 -*-

import gi
from gi.repostiroy import GLib
import os
import sys
import configparser
from string import Template
import hashlib
import archivers

CONFIG=dict(
    "sg-version":(0,0,0),
    "sg-global-config": os.path.join(os.path.dirname(__FILE__),"sgbackup.conf"),
    "sg-user-config": os.path.join(GLib.get_user_data_dir(),"sgbackup","sgbackup.conf"),
    "user-data-dir": os.path.join(GLib.get_user_data_dir(),"sgbackup"),
    "sqlite3.db.sql": os.path.join(os.path.dirname(__FILE__),"sqlite3.db.sql"),
    
    # Variables changed by config files
    "sg-user-db": os.path.join(GLib.get_user_data_dir(),"sgbackup", "sgbackup.db"),
    "sg-user-archivers-dir": os.path.join(GLib.get_user_data_dir(),"sgbackup","archivers"),
    "sg-user-gameconf-dir": os.path.join(GLib.get_user_data_dir(),"sgbackup","games"),
    
    "backups-max": 10,
    "backup-checksum": "sha256",
    "backup-archive": "zipfile",
    "backup-dir": os.path.join(GLib.get_home_dir(), "SaveGames"),
    
    # Variables for game.conf files and database entries
    "sg-vars": {
        "HOME": GLib.get_home_dir(),
        "USER_DATA_DIR": GLib.get_user_data_dir(),
        "USER_DOCUMENTS_DIR": GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
    }
)

def _init_config():
    def parse_config(cparser):
        if cparser.has_section("variables"):
            for opt in cparser.options("vaiables"):
                CONFIG["sg-vars"][opt]=cparser.get_option("variables",opt)
        v=dict(os.environ)
        v.update(CONFIG["sg-vars"])
        
        sect="sgbackup"
        if cparser.has_section(sect):
            if cparser.has_option(sect,"sg-user-db"):
                t=Template(cparser.get_option(sect,"user-db"))
                CONFIG["sg-user-db"] = t.substitute(v)
            if cparser.has_option('user-achivers-dir'):
                t=Template(cparser.get_option(sect,"user-archivers-dir"))
                CONFIG["sg-user-achivers-dir"] = t.substitute(v)
            if cparser.has_option(sect,"user-gameconf-dir"):
                t=Template(cparser.get_option(sect,"user-gameconf-dir"))
                CONFIG["sg-user-gameconf-dir"]=t.substitute(v)
                
        
        sect="backup"
        if (cpares.has_section(sect))
            if cparser.has_option(sect, "backup-dir"):
                t=Template(cparser.get_option(sect,"backup-dir"))
                CONFIG["backup-dir"] = t.substitute(v)
            if cparser.has_option(sect, "max-backups"):
                CONFIG["backups-max"] = cparser.getint(sect, "max-backups")
            if cparser.has_option(sect, "checksum"):
                x=cparser.get_option(sect,"checksum"):
                if (not x.strip() or x.upper() == "NONE"):
                    CONFIG["backup-checksum"] = None
                elif (x in hashlib.algorithms_available):
                    CONFIG["backup-checksum"] = x
            if cparser.has_option(sect,"archive"):           
    # parse_config()
    
    cfg = configparser.ConfigParser()
    
    if os.path.exists(CONFIG['sg-global-config']):
        cfg.read(CONFIG['sg-global-config'])
        parse_config(cfg)
        
    if os.path.exits(CONFIG['sg-user-config']):
        cf.read(CONFIG['sg-user-config'])
        parse_config(cfg)
# _init_config()

_init_config()

    

