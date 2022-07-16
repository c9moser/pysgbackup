#-*- coding:utf-8 -*-

import os
import sys
import zipfile
import tarfile

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
        
    def backup(self,filename,root_dir,backup_dir):
        pass
        
    def restore(self):
        pass
        
    
    @property
    def known_extensions(self):
        return []
        
    @property
    def extension(self):
        return None
# ProgramArchiver class
        
class TarFileArchiver(ArchiverBase):
    def __init__(self):
        ArchiverBase.__init__(self,'tarfile')
        
    def backup(self,filename,root_dir,backup_dir):
        if os.path.exists(os.path.join(root_dir,backup_dir)):
            cwd = os.getcwd()
            
            os.chdir(root_dir)
            if not os.path.exists(os.path.dirname(filename)):
                os.path.makedirs(os.path.dirname(filename))
            
            archive = tarfile.TarFile(name=filename,mode='w',dereference=True)
            archive.add(backup_dir,recursive=True)
            
            os.chdir(cwd)
            return True
        return False
        
    def restore(self,filename,root_dir):
        if not os.path.isfile(filename):
            return False
            
        if not os.path.exists(root_dir):
            os.path.makedirs(root_dir)
            
        archive = tarfile.TarFile(name=filename,mode='r',dereference=True)
        archive.extractall(path=root_dir)
        return True
        
    @property
    def known_extensions(self):
        return ["tar"]
        
    @property
    def extension(self):
        return "tar"
# TarFileArchiver class

class _ZipFileListFiles(object):
    def __init__(self,root_dir,rel_dir):
        self.__files=[]
        
        for i in os.path.listdir(os.path.join(root_dir,rel_dir)):
            if (i == '.' or i == '..'):
                continue
            if os.path.isdir(os.path.join(root_dir,rel_dir,i)):
                x = _ZipFileListFiles(root_dir,os.path.join(rel_dir,i))
                self.__files.append(x.files)
            if (os.path.isfile(i)):
                self.__files.append(os.path.join(rel_dir,i))
        
    @property
    def files(self):
        return sorted(self.__files)
    
        
class ZipFileArchiver(ArchiverBase):
    def __init__(self):
        ArchiverBase.__init__(self,'zipfile')
        self.__compression=config.CONFIG['zipfile-compression']
        self.__compresslevel=config.CONFIG['zipfile-compresslevel']
        
    def backup(self,filename,root_dir,backup_dir):
        if os.path.isdir(root_dir) and os.path.exists(os.path.join(root_dir,backup_dir)):
            cwd = os.getcwd()
            os.chdir(root_dir)
            
            if config.CONFIG['verbose']:
                print ('[zipfile:create] {0}'.format(filename))
            try:
                with zipfile.ZipFile(filename,'w',
                                     compression=self.compression,
                                     comporesslevel=self.compresslevel) as archive:
                        zfiles = _ZipFileListFiles(root_dir,rel_dir)
                        for i in zfiles.files:
                            if sys.platform == 'win32':
                                arcname = i.replace('\\','/')
                            else:
                                arcname = i
                            
                            if (config.CONFIG['verbose']):
                                print(['[zipfile:add] {0}'.format(i)])
                            archive.write(i,arcname=arcname)
                os.chdir(cwd)
                return True
            except Exception as error:
                print (error,file=sys.stderr)
        return False
    # backup()

    def restore(self,filename,root_dir):
        if os.path.isfile(filename): 
            if not os.path.exists(root_dir):
                os.makedirs(root_dir)
            
            os.chdir(root_dir)
            
            try:
                if config.CONFIG['verbose']:
                    print('[zipfile:extract] {0}'.format(filename))
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
        
# ZipFileArchiver class
