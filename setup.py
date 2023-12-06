#!/usr/bin/env python

import os
import sys
from setuptools import setup
from string import Template
import subprocess
import bz2

PACKAGE_ROOT=os.path.dirname(__file__)

cygpath=None
if 'MSYSTEM' in os.environ and os.environ['MSYSTEM'] in ('MINGW','MINGW64','CLANG64','UCRT64'):
    HAVE_MSYS = True
    _test = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))),'usr','bin','cygpath.exe')
    if os.path.isfile(_test):
        cygpath = _test
    del _test
else:
    HAVE_MSYS = False

scripts=[]
def get_scripts():
    global PACKAGE_ROOT
    global HAVE_MSYS
    global cygpath

    if sys.platform == 'win32':
        bin_scripts = [('bin/sgbackup.bat',False)]
        if HAVE_MSYS and cygpath:
            bin_scripts.append(('bin/sgbackup',True))
    else:
        bin_scripts = [('bin/sgbackup',False)]

    if cygpath:
        try:
            proc = subprocess.run([cygpath,"-u",sys.executable],capture_output=True)
            if proc.returncode == 0:
                PYTHON_CYGPATH = proc.stdout.decode('utf-8').rstrip()
            else:
                cygpath = None
        except Exception as ex:
            cygpath = None

    for bs,use_cygpath in bin_scripts:
        if os.path.isfile(os.path.join(PACKAGE_ROOT,bs + '.in')):
            with open(os.path.join(PACKAGE_ROOT,bs + '.in'),'r') as ifile:
                with open(os.path.join(PACKAGE_ROOT,bs),'w') as ofile:
                    if not use_cygpath:
                        bs_vars = {
                            'PYTHON':sys.executable
                        }
                        ofile.write(Template(ifile.read()).safe_substitute(bs_vars))
                        scripts.append(bs)
                    elif cygpath:
                        bs_vars = {
                            'PYTHON': PYTHON_CYGPATH
                        }
                        ofile.write(Template(ifile.read()).safe_substitute(bs_vars))
                        scripts.append(bs)

    return scripts

def get_help_files():
    global PACKAGE_ROOT

    help_files=[]
    help_dir = os.path.join(PACKAGE_ROOT,'sgbackup','help')

    for i in os.listdir(help_dir):
        if not i.endswith('.txt'):
            continue

        fn = os.path.join(help_dir,i)
        fn_bz2 = (fn + '.bz2')
        with bz2.open(fn_bz2,'wt',9,'utf-8') as ofile:
            with open(fn,'r') as ifile:
                ofile.write(ifile.read())
        help_files.append(os.path.basename(fn_bz2))

    return help_files

setup(
    name='pysgbackup',
    version='0.0.10',
    description='A commandline backup tool for savegames.',
    author="Christian Moser",
    author_email="c9moser@gmx.at",
    packages=[
        'sgbackup',
        'sgbackup.archiver',
        'sgbackup.config',
        'sgbackup.locale',
        'sgbackup.commands',
        'sgbackup.help',
        'sgbackup.plugins',
        'sgbackup.plugins.ftp',
        'sgbackup.plugins.checksum',
    ],
    platforms=['win32'],
    package_data={
        'sgbackup.help':get_help_files()
    },
    scripts=get_scripts()
)
