# -*- coding: utf-8 -*-
# author: Christian Moser
# file sgbackup/archiver/tarfilearchiver.py
# module sgbackup.archiver.tarfilearchiver

import tarfile
from ._archiver import ArchiverBase
import os

class TarfileArchiverBase(ArchiverBase):
    __name__ = "sgbackup-archiver-tarfilearchiver-TarArchiverBase"
    def __init__(self,app,id,extension,extensions=[],compression=""):
        ArchiverBase.__init__(self,app,id,extension,extensions)

        self.__compression = compression

    def file_is_archive(self,filename):
        return  (tarfile.is_tarfile(filename) and ArchiverBase.file_is_archive(self,filename))

    def do_backup(self, game, filename):
        if not os.path.exists(os.path.join(game.savegame_root,game.savegame_dir)):
            if self.application.config.verbose:
                print("[{game_id}] No SaveGame dir does not exist! SKIPPING!!!".format(game_id=game.game_id))
            return
        
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        if self.__compression:
            open_mode = 'w:' + self.__compression
        else:
            open_mode = 'w'

        with tarfile.open(filename,open_mode) as backup:
            backup.add(os.path.join(game.savegame_root,game.savegame_dir),arcname=game.savegame_dir)
        
    def do_restore(self,game,filename):
        if not os.path.exists(game.savegame_root):
            os.makedirs(game.savegame_root)

        with tarfile.open(filename,'r:' + self.__compression) as backup:
            backup.extractall(path=game.savegame_root)

class TarfileArchiver(TarfileArchiverBase):
    __name__ = "sgbackup-archiver-tarfilearchiver-TarArchiver"

    def __init__(self,app):
        TarfileArchiverBase.__init__(self,app,'tarfile','tar',['tar'])

class TarfileBz2Archiver(TarfileArchiverBase):
    __name__ = "sgbackup-archiver-tarfilearchiver-TarBz2Archiver"

    def __init__(self,app):
        TarfileArchiverBase.__init__(self,app,'tarfile:bz2','tbz',['tbz','tar.bz2'],"bz2")

class TarfileGzArchiver(TarfileArchiverBase):
    __name__ = "sgbackup-archiver-tarfilearchiver-TarGzArchiver"

    def __init__(self,app):
        TarfileArchiverBase.__init__(self,app,'tarfile:gz','tgz',['tgz','tar.gz'],'gz')

class TarfileXzArchiver(TarfileArchiverBase):
    __name__ = "sgbackup-archiver-tarfilearchiver-TarXzArchiver"

    def __init__(self,app):
        TarfileArchiverBase.__init__(self,app,'tarfile:xz','txz',['txz','tar.xz'],'xz')
