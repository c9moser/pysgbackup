#-*- coding: utf-8 -*-

import os
import configparser
import importlib
import sys
from .. import config
from ._archiver import ArchiverBase,ProgramArchiver,TarFileArchiver,ZipFileArchiver

ARCHIVERS={
    'tarfile': {
        'builtin': True,
        'class': TarFileArchiver
    },
    'zipfile': {
        'builtin': True,
        'class': ZipFileArchiver,
    }
}

def _parse_conf(filename):
    parser = configparser.ConfigParser()
    parser.read(filename)
    
    conf={
        'builtin':False,
        'archiver': os.path.splitext(os.path.basename(filename))[0]
    }

    sect='archiver'
    if parser.has_section(sect):
        if parser.has_option(sect,'cygpath'):
            conf['cygpath']=parser.get(sect,'cygpath')
        if parser.has_option(sect,'executable'):
            conf['executable'] = parser.get(sect,'executable')
        if parser.has_option(sect,'create'):
            conf['create'] = parser.get(sect,'create')
        if parser.has_option(sect,'extract'):
            conf['extract'] = parser.get(sect,'extract')
        if parser.has_option(sect,'verbose'):
            conf['verbose'] = parser.get(sect,'verbose')
        
        if parser.has_option(sect,'change-directory'):
            conf['change-directory'] = parser.getboolean(sect,'change-directory')
        else:
            conf['change-directory'] = False
            
        if parser.has_option(sect,'extension'):
            raw_ext=parser.get(sect,'extension')
            if raw_ext.startswith('.'):
                ext = raw_ext[1:]
            else:
                ext = raw_ext
            conf['extension'] = ext
            conf['known-extensions'] = [ext]
        if parser.has_option(sect,'known-extensions'):
            known_extensions=[]
            for i in parser.get(sect,'known-extensions').split(';'):
                if i.startswith('.'):
                    ext = i[1:]
                else:
                    ext = i
                known_extensions.append(ext)
                
            if not known_extensions:
                known_extensions=[conf['extension']]
            conf['known-extensions'] = known_extensions
    return conf
    
def _validate_conf_keys(conf):
    if not conf:
        return False
        
    keys=[
        'archiver',
        'executable',
        'create',
        'extract',
        'extension'
    ]

    for k in keys:
        if k not in conf:
            return False
    return True
        

# check global archivers
for i in os.listdir(os.path.dirname(__file__)):
    if not i.startswith('_') and not i.startswith('.'):
        if i.endswith('.archiver'):
            conf=_parse_conf(os.path.join(os.path.dirname(__file__),i))
            if (_validate_conf_keys(conf)):
                archiver_id=i[0:-9]
                ARCHIVERS[archiver_id]=conf
                for e in conf['known-extensions']:
                    config.CONFIG['archivers'][e]={'archiver':archiver_id}

# check local archivers
if os.path.isdir(config.CONFIG['user-archivers-dir']):
    for i in os.listdir(config.CONFIG['user-archivers-dir']):
        if i.startswith('.') or i.startswith('_'):
            continue            
        if i.endswith('.archiver'):
            conf=_parse_conf(os.path.join(config.CONFIG['user-archivers-dir'],i))
            if (_validate_conf_keys(conf)):
                archiver_id=i[0:-9]
                ARCHIVERS[archiver_id]=conf
                for e in conf['known-extensions']:
                    config.CONFIG['archivers'][e]={'archiver':archiver_id}

def get_archiver(archiver_id=None):
    if not archiver_id:
        archiver_id=config.CONFIG['backup.archiver']
        
    if not archiver_id in ARCHIVERS.keys():
        return None
        
    archiver=None
    
    if ARCHIVERS[archiver_id]['builtin']:
        archiver=ARCHIVERS[archiver_id]['class']()
    else:
        archiver=ProgramArchiver(archiver_id,ARCHIVERS[archiver_id])
        
    return archiver
# get_archiver()

def list_archivers():
    return sorted(ARCHIVERS.keys())
    
def update_archivers(global_archivers=False):
    # check for tar archiver
    tar_exe = None
    archiver_dir = os.path.dirname(__file__)
    if global_archivers:
        odir = config.CONFIG['global-archivers-dir']
    else:
        odir = config.CONFIG['user-archivers-dir']
    if sys.platform == 'win32':
        cygpath_exe = None
        cygpath_ck_exe = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))),'usr','bin','cygpath.exe')
        if os.path.isfile(cygpath_ck_exe):
            cygpath_exe = cygpath_ck_exe
        
        tar_ck_exe = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))),'usr','bin','tar.exe')
        if os.path.isfile(tar_ck_exe):
            tar_exe = tar_ck_exe
    else:
        for p in os.environ['PATH'].split(':'):
            if os.path.isfile(os.path.join(p,'tar')):
               tar_exe = os.path.join(p,'tar')
               break 
            
    if tar_exe and sys.platform == 'win32':
        if cygpath_exe:
            archiver_in = [
                'tar.archiver.w32.in',
                'tar.bz2.archiver.w32.in',
                'tar.gz.archiver.w32.in',
                'tar.xz.archiver.w32.in',
                'tbz.archiver.w32.in',
                'tgz.archiver.w32.in',
                'txz.archiver.w32.in'
            ]
        
            for i in archiver_in:
                archiver_file=i[:-7]
                
                if (config.CONFIG['verbose']):
                    print("<archiver:update> {}".format(archiver_file[:-9]))
                    
                with open(os.path.join(archiver_dir,i),'r') as ifile:
                    s=ifile.read()
                s = s.replace('__CYGPATH__',cygpath_exe)
                s = s.replace('__EXECUTABLE__',tar_exe)

                try:
                    with open(os.path.join(odir,archiver_file),'w') as ofile:
                        ofile.write(s)
                except Exception as error:
                    print('Unable to write to archivers dir! ({})'.format(error),file=sys.stderr)
                    return
        elif tar_exe:
            archiver_in = [
                'tar.archiver.in',
                'tar.bz2.archiver.in',
                'tar.gz.archiver.in',
                'tar.xz.archiver.in',
                'tbz.archiver.in',
                'tgz.archiver.in',
                'txz.archiver.in'
            ]
                
            for i in archiver_in:
                archiver_file = i[:-3]
                
                if config.CONFIG['verbose']:
                    print('<archiver:update> {}'.format(archiver_file[:-9]))
                    
                with open(os.path.join(archiver_dir,i),'r') as ifile:
                    s=ifile.read()
                s = s.replace('__EXECUTABLE__',tar_exe)
                
                try:
                    with open(os.path.join(odir,archiver_file),'w') as ofile:
                        ofile.write(s)
                except Exception as error:
                    print('Unable to write to archivers dir! ({})'.format(error))
                    return
                    
    #check for win32 archivers
    if sys.platform == 'win32':
        winrar_exe = os.path.join(os.environ['SYSTEMDRIVE'],"Program Files","WinRAR","WinRAR.exe")
        if os.path.isfile(winrar_exe):
            if config.CONFIG['verbose']:
                print('<archiver:update> rar')
                
            with open(os.path.join(archiver_dir,'rar.archiver.w32.in'),'r') as ifile:
                s = ifile.read()
                
            s = s.replace('__EXECUTABLE__',winrar_exe)
            
            try:
                with open(os.path.join(odir,'rar.archiver'),'w') as ofile:
                    ofile.write(s)
            except Exception as error:
                print('Unable to write to archivers dir! ({})'.format(error))
                return
                
        sevenzip_search_path=[
            os.path.join(os.environ['SYSTEMDRIVE'],'Program Files','7z','7z.exe'),
            os.path.join(os.environ['SYSTEMDRIVE'],'Program Files (x86)','7z','7z.exe')
        ]
        sevenzip_exe = ''
        for i in sevenzip_search_path:
            if os.path.isfile(i):
                sevenzip_exe = i
                break
                
        if sevenzip_exe:
            if config.CONFIG['verbose']:
                print('<archiver:update> 7z')
            with open(os.path.join(archiver_dir,'7z.archiver.w32.in'),'r') as ifile:
                s = ifile.read()
            
            s = s.replace('__EXECUTABLE__',sevenzip_exe)
            
            with open(os.path.join(odir,'7z.archiver'),'w') as ofile:
                ofile.write(s)
        
# update_archivers
