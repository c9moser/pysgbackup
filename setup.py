from distutils.core import setup
import os
import sys

import sgbackup

scripts=[]

if sys.platform == 'win32':
    sgbackup_bat=os.path.join(os.path.dirname(__file__),'bin','sgbackup.bat')
    with open('.'.join((sgbackup_bat,'in')),'r') as ifile:
        s = ifile.read()
        s = s.replace("__PYTHON_EXEC__",sys.executable)
        with open(sgbackup_bat,"w") as ofile:
            ofile.write(s)
    scripts.append('bin/sgbackup.bat')
scripts.append('bin/sgbackup')

setup(name="pysqgbackup",
      version=".".join((str(i) for i in sgbackup.config.CONFIG["version"])),
      description="Tool to manage SaveGame backups",
      author="Christian Moser",
      author_email="c9moser@gmx.at",
      packages=[
        "sgbackup",
        "sgbackup.archivers",
        "sgbackup.games",
        "pysgbackup"],
      scripts=scripts,
      include_package_data='true',
      package_data={'sgbackup':["*.sql",'*.conf'],
                    'sgbackup.games': ['*.conf'],
                    'sgbackup.archivers': ['*.conf']})

