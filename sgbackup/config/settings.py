# -*- coding:utf-8 -*-
# author: Christian Moser
# file: sgbackup/_conf/settings.py
# module: sgbackup._conf.sysconf
# license: GPL

import os
import sys

from gi.repository import GLib

VERSION_MAJOR=0
VERSION_MINOR=0
VERSION_MICRO=10

VERSION_NUMBER=(VERSION_MAJOR,VERSION_MINOR,VERSION_MICRO)
VERSION=".".join((str(i) for i in (VERSION_MAJOR,VERSION_MINOR,VERSION_MICRO)))

PACKAGE="pysgbackup"
GETTEXT_PACKAGE=PACKAGE

LOCALEDIR=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"locale")
LANGUAGES=["C","de"]

if sys.platform == "win32":
    PLATFORM_WIN32 = True
    USER_HOME_DIR = os.environ["USERPROFILE"]
    USER_USE_ONEDRIVE = os.path.isdir(os.path.join(USER_HOME_DIR,"OneDrive"))
    if USER_USE_ONEDRIVE:
        USER_ONEDRIVE_DIR = os.path.join(USER_HOME_DIR,"OneDrive").replace("/","\\")
    else:
        USER_ONEDRIVE_DIR = USER_HOME_DIR
elif sys.platform.lower() in ['linux','freebsd']:
    PLATFORM_WIN32 = False
    USER_HOME_DIR = GLib.get_home_dir()
    USER_USE_ONEDRIVE = False
    USER_ONEDRIVE_DIR = USER_HOME_DIR
else:
    print("Configuring for unsupported platform {}!".format(sys.platform),file=sys.stderr)


USER_DOCUMENTS_DIR = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS)
USER_DATA_DIR = os.path.join(GLib.get_user_data_dir(),"pysgbackup")
USER_CONFIG_DIR = os.path.join(GLib.get_user_config_dir(),"pysgbackup")

if sys.platform == "win32":
    LOCALEDIR = LOCALEDIR.replace("/","\\")
    USER_DATA_DIR = USER_DATA_DIR.replace("/","\\")
    USER_CONFIG_DIR = USER_CONFIG_DIR.replace("/","\\")

def get_default_pager():
    if PLATFORM_WIN32:
        default_pager = "more.com"
    else:
        if 'PAGER' in os.environ:
            default_pager = os.environ['PAGER']
        else:
            pager_found = False
            for i in ['less','more']:
                for path in os.environ['PATH'].split(':'):
                    if os.path.isfile(os.path.join(path,i)):
                        default_pager = os.path.join(path,i)
                        pager_found = True
                        break
            if not pager_found:
                default_pager = "less"

    return default_pager
