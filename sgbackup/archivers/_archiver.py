#-*- coding:utf-8 -*-

import os
import zipfile
import tarfile

from .. import config

class ArchiverBase(object):
    def __init__(self,archiver_id,config):
        object.__init__(self)
        
        self.__id = archiver_id
        
    @property
    def id(self):
        return self.__id
        
    def backup(self,filename,root_dir,backup_dir):
        raise NotImplementedError('\'Archive.backup()\' is not implmented!')
        
    def restore(self,filename,root_dir):
        raise NotImplementedError('\'Archive.restore()\' is not implemented!')
        
# ArchiverBase class

class ProgramArchiver(ArchiverBase):
    def __init__(self,archiver_id,config):
        ArchiverBase.__init__(self,archiver_id,config)
        
    def backup(self,filename,root_dir,backup_dir):
        pass
        
    def restore(self):
        pass
        
    @property
    def extension(self):
        return
# ProgramArchiver class
        
class TarFileArchiver(ArchiverBase):
    def __init__(self,config):
        ArchiverBase.__init__(self,'tarfile',config)
        
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

class ZipFileArchiver(ArchiverBase):
    def __init__(self,config):
        ArchiverBase.__init__(self,'zipfile')
        
    def backup(self,filename,root_dir,backup_dir):            
        if os.path.isdir(root_dir) and os.path.exists(os.path.join(root_dir,backup_dir)):
            cwd = os.getcwd()
            os.chdir(root_dir)
            
            zipfile.ZipFile(filename,'w',
                            compression=config.CONFIG['zipfile-compression'],
                            comporession_level=config.CONFIG['zipfile-copmression-level'])
            #TODO: backup files
            
            os.chdir(cwd)
    # backup()

    def restore(self,filename,root_dir,backup_dir):
        pass
        
    @property
    def known_extensions(self):
        return [self.extension]
        
    @property
    def extension(self):
        return "zip"
# ZipFileArchiver class
