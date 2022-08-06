#-*- coding:utf-8 -*-

import os
import sys
import zipfile
import tarfile
import subprocess
import string

from .. import config

class ArchiverBase(object):
    def __init__(self,archiver_id):
        object.__init__(self)
        
        self.__id = archiver_id
        
    @property
    def id(self):
        return self.__id
        
    def backup(self,filename,root_dir,backup_dir):
        raise NotImplementedError('\'Archive.backup()\' is not implmented!')
        
    def restore(self,filename,root_dir):
        raise NotImplementedError('\'Archive.restore()\' is not implemented!')
        
    @property
    def known_extensions(self):
        return []
        
    @property
    def extension(self):
        return ""            
# ArchiverBase class

class ProgramArchiver(ArchiverBase):
    def __init__(self,archiver_id,conf):
        ArchiverBase.__init__(self,archiver_id)
    
        self.__archiver = conf['archiver']
        self.__executable = conf['executable']    
        self.__create = conf['create']
        self.__restore = conf['extract']
        self.__extension = conf['extension']
        self.__known_extensions = conf['known-extensions']
        self.__change_directory = conf['change-directory']
    
        if ('verbose' in conf and conf['verbose']):
            self.__verbose = conf['verbose']
        else:
            self.__verbose = ""
            
        if ('cygpath' in conf and conf['cygpath']):
            self.__cygpath = conf['cygpath']
        else:
            self.__cygpath = ''
        
    # __init__()
    
    @property
    def archiver(self):
        return self.__archiver
    
    @property
    def executable_raw(self):
        return self.__executable
        
    @property
    def executable(self):
        return os.path.normpath(self.__executable)
        
    @property
    def _create_template(self):
        return '"{0}" {1}'.format(self.executable,self.__create)
    
    @property
    def _restore_template(self):
        return '"{0}" {1}'.format(self.executable,self.__restore)
        
    @property
    def cygpath(self):
        if self.__cygpath:
            return os.path.normpath(self.__cygpath)
        return ""
        
    @property
    def change_directory(self):
        return self.__change_directory
        
    @property
    def extension(self):
        return self.__extension
        
    @property
    def known_extensions(self):
        return self.__known_extensions
        
    @property
    def verbose(self):
        return self.__verbose
    
    def _save_win32_path(self,path):
        return path.replace('/','\\')
        
    def _get_template_variables(self,filename,root_dir,backup_dir=''):
        def _cygpath(path):
            if not path:
                return ""
            if not self.cygpath:
                # msys fix
                if sys.platform == 'win32':
                    return self._save_win32_path(os.path.normpath(path))
                return os.path.normpath(path)
            
            proc = subprocess.run([self.cygpath,path],capture_output=True,text=True)
            s=proc.stdout
            if s.startswith("b'"):
                s = s[2:-3]
            elif s.endswith('\\n'):
                s = s[:-2]
            else: 
                s= s[:-1]
                
            return s
        # _cygpath()
            
        if config.CONFIG['verbose']:
            verbose = self.verbose
        else:
            verbose = ""
        
        tvars = dict(os.environ)
        tvars.update(config.CONFIG['template-variables'])
        tvars.update({'FILENAME': _cygpath(filename),
                      'ROOT_DIR': _cygpath(root_dir),
                      'BACKUP_DIR': _cygpath(backup_dir),
                      'VERBOSE': verbose})
        return tvars
    # _get_template_variables()
        
    def _get_backup_command(self,filename,root_dir,backup_dir):
        tvars = self._get_template_variables(filename,root_dir,backup_dir)
        t = string.Template(self._create_template)
        return t.substitute(tvars)
    # _get_backup_command()
          
    def _get_restore_command(self,filename,root_dir):
        tvars = self._get_template_variables(filename,root_dir)
        t = string.Template(self._restore_template)
        return t.substitute(tvars)
    # _get_restore_command()
    
    def backup(self,filename,root_dir,backup_dir,stdout=sys.stdout,stderr=sys.stderr):
        cmd = self._get_backup_command(filename,root_dir,backup_dir)
        cwd = os.getcwd()
        
        if self.change_directory:
            os.chdir(root_dir)
            
        if config.CONFIG['verbose']:
            print("<{0}:create> {1}".format(self.archiver,filename))
        try:
            cproc = subprocess.run(cmd,stdout=stdout,stderr=stderr)
        except subprocess.CalledProcessError as error:
            print('Backup failed! ({0})'.format(error))
            if self.change_directory:
                os.chdir(cwd)
            return False
            
        if self.change_directory:
            os.chdir(cwd)
        return True
    # backup()
    
    def restore(self,filename,root_dir,stdout=sys.stdout,stderr=sys.stderr):
        cmd = self._get_restore_command(filename,root_dir)
        cwd = os.getcwd()
        
        if not os.path.exists(root_dir):
            try:
                os.makedirs(root_dir)
            except Exception as error:
                print('Creating directory \'{0}\' failed! ({1})',format(root_dir,error),file=stderr)
                return False
        
        if self.change_directory:
            os.chdir(root_dir)
            
        if config.CONFIG['verbose']:
            print("<{0}:extract> {1}".format(self.archiver,filename))
        try:
            cproc = subprocess.run(cmd,stdout=stdout,stderr=stderr)
        except subprocess.CalledProcessError as error:
            print('Backup restore failed! ({0})'.format(error),file=stderr)
            if self.change_directory:
                os.chdir(cwd)
            return False
            
        if self.change_directory:
            os.chdir(cwd)
        return True
    # restore()
# ProgramArchiver class
        
class TarFileArchiver(ArchiverBase):
    def __init__(self):
        ArchiverBase.__init__(self,'tarfile')
        
    @property
    def known_extensions(self):
        return ['tar']
        
    @property
    def extension(self):
        return "tar"
        
        
    def backup(self,filename,root_dir,backup_dir):
        if os.path.exists(os.path.join(root_dir,backup_dir)):
            cwd = os.getcwd()
            
            os.chdir(root_dir)
            
            if not os.path.exists(os.path.dirname(filename)):
                os.path.makedirs(os.path.dirname(filename))
            
            if config.CONFIG['verbose']:
                print('<tarfile:create>: {0}'.format(filename))
            archive = tarfile.open(filename,'w')
            archive.add(backup_dir,recursive=True)
            
            os.chdir(cwd)
            return True
        return False
    # backup()
    
    def restore(self,filename,root_dir):
        if not os.path.isfile(filename):
            return False
            
        if not os.path.exists(root_dir):
            os.path.makedirs(root_dir)
            
        if config.CONFIG['verbose']:
            print('<tarfile:extract> {0}'.format(filename))
        archive = tarfile.open(filename,'r')
        archive.extractall(path=root_dir)
        return True
    # restore()
# TarFileArchiver class

class _ZipFileListFiles(object):
    def __init__(self,root_dir,rel_dir):
        self.__files=[]
        
        for i in os.listdir(os.path.join(root_dir,rel_dir)):
            if (i == '.' or i == '..'):
                continue
            fname=os.path.join(root_dir,rel_dir,i)
            if os.path.isdir(fname):
                x = _ZipFileListFiles(root_dir,os.path.join(rel_dir,i))
                self.__files += x.files
            elif os.path.isfile(fname):
                self.__files.append(os.path.join(rel_dir,i))
        
    @property
    def files(self):
        return sorted(self.__files)
# _ZipFileListFiles class    
        
class ZipFileArchiver(ArchiverBase):
    def __init__(self):
        ArchiverBase.__init__(self,'zipfile')
        self.__compression=config.CONFIG['zipfile.compression']
        self.__compresslevel=config.CONFIG['zipfile.compresslevel']
    # __init__()
    
    @property
    def known_extensions(self):
        return [self.extension]
        
    @property
    def extension(self):
        return "zip"
        
    @property
    def compression(self):
        return self.__compression

    @property
    def compresslevel(self):
        return self.__compresslevel
            
    def backup(self,filename,root_dir,backup_dir):
        if os.path.isdir(root_dir) and os.path.exists(os.path.join(root_dir,backup_dir)):
            cwd = os.getcwd()
            os.chdir(root_dir)
            
            if config.CONFIG['verbose']:
                print ('<zipfile:create> {0}'.format(filename))
            try:
                with zipfile.ZipFile(filename,'w',
                                     compression=self.compression,
                                     compresslevel=self.compresslevel) as archive:
                        zfiles = _ZipFileListFiles(root_dir,backup_dir)
                        for i in zfiles.files:
                            if sys.platform == 'win32':
                                arcname = i.replace('\\','/')
                            else:
                                arcname = i
                            
                            if (config.CONFIG['verbose']):
                                print('<zipfile:add> {0}'.format(i))
                            archive.write(i,arcname=arcname)
            except Exception as error:
                print (error,file=sys.stderr)
                os.chdir(cwd)
                return False
                
            os.chdir(cwd)
            return True
    # backup()

    def restore(self,filename,root_dir):
        if os.path.isfile(filename): 
            if not os.path.exists(root_dir):
                os.makedirs(root_dir)
            
            try:
                if config.CONFIG['verbose']:
                    print('<zipfile:extract> {0}'.format(filename))
                with zipfile.ZipFile(filename,'r',
                                     compression=self.compression,
                                     compresslevel=self.compresslevel) as archive:
                    if not os.path.exists(root_dir):
                        os.path.makedirs(root_dir)
                    archive.extractall(root_dir)
                    return True
            except Exception as error:
                print(error,file=sys.stderr)
        return False
    # restore()
# ZipFileArchiver class
