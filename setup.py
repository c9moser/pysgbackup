#!/usr/bin/env python
#-*- coding:utf-8 -*-

#from setuptools import setup
from distutils.core import setup
import os
import sys

try:
    from . import sgbackup
except ImportError:
    import sgbackup


try:
    import gi
    gi.require_version('GLib','2.0')
    gi.require_version('Gtk','3.0')
except ImportError as err:
    print("\"GObject Introspection\" not installed!")
    sys.exit(3)

scripts=[]

if sys.platform == 'win32':
    import string
    from ctypes import windll

    def get_drives():
        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(letter)
            bitmask >>= 1

        return drives
    #get_drives()
    
    archiver_path=os.path.join(os.path.dirname(__file__),'sgbackup','archivers')
    
    sgbackup_bat=os.path.join(os.path.dirname(__file__),'bin','sgbackup.bat')
    with open('.'.join((sgbackup_bat,'in')),'r') as ifile:
        s = ifile.read()
        s = s.replace("__PYTHON_EXEC__",sys.executable)
        with open(sgbackup_bat,"w") as ofile:
            ofile.write(s)
    scripts.append('bin/sgbackup.bat')
    
    pysgbackup_bat=os.path.join(os.path.dirname(__file__),'bin','pysgbackup.bat')
    with open('.'.join((pysgbackup_bat,'in')),'r') as ifile:
        s = ifile.read()
        s = s.replace("__PYTHON_EXEC__",sys.executable)
        with open(pysgbackup_bat,"w") as ofile:
            ofile.write(s)
    scripts.append('bin/pysgbackup.bat')
        
scripts.append('bin/sgbackup')
scripts.append('bin/pysgbackup')

setup(name="pysgbackup",
      version=".".join((str(i) for i in sgbackup.config.CONFIG["version"])),
      description="Tool to manage SaveGame backups",
      author="Christian Moser",
      author_email="c9moser@gmx.at",
      packages= ['sgbackup',
                 'sgbackup.archivers',
                 'sgbackup.games',
                 'sgbackup.plugins',
                 'sgbackup.plugins.ftp',
                 'sgbackup.plugins.checksum',
                 'sgbackup.plugins.mkiso',
                 'pysgbackup'
      ],
      scripts=scripts,
      include_package_data=True,
      package_data={'sgbackup':["*.sql","*.txt"],
                    'sgbackup.games': ['*.game','*.game.in'],
                    'sgbackup.archivers': ['*.archiver.in','*.archiver.w32.in'],
                    'sgbackup.plugins.checksum': ['*.txt'],
                    'sgbackup.plugins.ftp': ['*.txt'],
                    'sgbackup.plugins.mkiso': ['*.bat','*.sh','*.txt'],
                    'pysgbackup' : ['*.ui']
      })

