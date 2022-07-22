from distutils.core import setup
import os
import sys

import sgbackup

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
    
    # check if we are installed in msys or similar
    if os.path.basename(os.path.basename(os.path.dirname(sys.executable))) == 'bin':
        msys_root = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
        msys_usr_bin = os.path.join(msys_root,'usr','bin')
        if os.path.isdir(msys_usr_bin):
            replace={"__CYGPATH__":''}
            cygpath_exe = ""
            if os.path.isfile(os.path.join(msys_usr_bin,'cygpath.exe')):
                cygpath_exe = os.path.join(msys_usr_bin,'cygpath.exe')
                replace['__CYGPATH__'] = cygpath_exe
            if os.path.isfile(os.path.join(msys_usr_bin,'tar.exe')):
                tar_exe = os.path.join(msys_usr_bin,'tar.exe')
                replace['__EXECUTABLE__'] = tar_exe
                
                for i in ['tar','tar.xz','txz','tar.gz','tgz','tar.bz2','tbz']:
                    with open(os.path.join(archiver_path,'.'.join((i,'archiver','w32','in'))),'r') as ifile:
                        s=ifile.read()
                    for k,v in replace.items():
                        s.replace(k,v)
                    with open(os.path.join(archiver_path,'.'.join((i,'archiver'))),'w') as ofile:
                        ofile.write(s)
                
    
scripts.append('bin/sgbackup')

setup(name="pysgbackup",
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
      package_data={'sgbackup':["*.sql"],
                    'sgbackup.games': ['*.game'],
                    'sgbackup.archivers': ['*.archiver']})

