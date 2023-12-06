# -*- coding:utf-8 -*-
#author: Christian Moser
#file: sgbackup/archiver/zipfilearchiver.py
#module: sgbackup.archiver.zipfilearchiver
#licenese: GPL

from gi.repository import GObject
from ._archiver import ArchiverBase
import zipfile
import os
import sys

import sgbackup
class ZipfileArchiver(ArchiverBase):
    CONFIG_SECTION="zipfileArchiver"

    __name__ = "sgbackup.archiver.zipfilearchiver.ZipfileArchiver"

    def __init__(self,app):
        ArchiverBase.__init__(self,app,"zipfile","zip",["zip"])

    @GObject.Property
    def compression(self):
        d = {
            'stored': zipfile.ZIP_STORED,
            'deflated': zipfile.ZIP_DEFLATED,
            'bzip2': zipfile.ZIP_BZIP2,
            'lzma': zipfile.ZIP_LZMA,
        }
        compression = self.application.config.get(self.CONFIG_SECTION,'compression',"deflated")
        if compression not in d:
            return zipfile.ZIP_DEFLATED
        return d[compression]
    
    @compression.setter
    def compression(self,comp):
        if isinstance(comp,str):
            c = ['stored','deflated','bzip2','lzma']
            if comp not in c:
                raise ValueError("\compression\" is not valid compression string!")
            sgbackup.app.config.set(self.CONFIG_SECTION,'compression',comp)
            return
        d = {
            zipfile.ZIP_STORED: 'stored',
            zipfile.ZIP_DEFLATED: 'deflated',
            zipfile.ZIP_BZIP2: 'bzip2',
            zipfile.ZIP_LZMA: 'lzma'
        }
        if comp not in d:
            raise ValueError("\"compression\" is not a valid ZipFile comression!")
        
        sgbackup.app.config.set(self.CONFIG_SECTION,'compression',d[comp])

    @GObject.Property(int)
    def compresslevel(self):
        cl = self.application.config.get(self.CONFIG_SECTION,'compresslevel',9)
        if self.compression == zipfile.ZIP_DEFLATED:
            if cl < 0:
                cl = 0
            elif cl > 9:
                cl = 9
        elif self.compression == zipfile.ZIP_BZIP2:
            if cl < 1:
                cl = 1
            elif cl > 9:
                cl = 9
        
        return cl
    
    @compresslevel.setter
    def compresslevel(self,cl):
        if self.compression == zipfile.ZIP_DEFLATED:
            if cl < 0:
                cl = 0
            elif cl > 9:
                cl = 9
        elif self.compression == zipfile.ZIP_BZIP2:
            if cl < 1:
                cl = 1
            elif cl > 9:
                cl = 9
        
        self.application.config.set(self.CONFIG_SECTION,'compresslevel',cl)


    def _list_files_to_backup(self,game):
        def parse_dir_tree(sgroot,sgdir,rel=None):
            if not rel:
                check_dir = os.path.join(sgroot,sgdir)
            else:
                check_dir = os.path.join(sgroot,sgdir,rel)

            ret = []
            
            for i in os.listdir(check_dir):
                if not rel:
                    x = i
                else:
                    x = os.path.join(rel,i)

                if i == "." or i == "..":
                    continue
                elif os.path.isdir(os.path.join(check_dir,i)):
                    ret.append((x,True))
                    ret += parse_dir_tree(sgroot,sgdir,x)
                else:
                    ret.append((x,False))

            return ret
        # parse_dir_tree()

        if not game.is_valid or not os.path.exists(os.path.join(game.savegame_root,game.savegame_dir)):
            return None
        elif os.path.isfile(os.path.join(game.savegame_root,game.savegame_dir)):
            return []
        elif os.path.isdir(os.path.join(game.savegame_root,game.savegame_dir)):
            return parse_dir_tree(game.savegame_root,game.savegame_dir)
        
        
    def do_backup(self, game, filename):
        if not os.path.exists(os.path.join(game.savegame_root,game.savegame_dir)):
            if self.application.config.verbose:
                print("[{game_id}] No SaveGame dir does not exist! SKIPPING!!!".format(game_id=game.game_id))
            return

        if not os.path.exists(game.backup_dir):
            os.makedirs(game.backup_dir)

        backup_files = self._list_files_to_backup(game)
        if not backup_files:
            print("No files to backup found for game \"{}\"! Skipping!".format(game.game_name),file=sys.stderr)
            return

        with zipfile.ZipFile(filename,mode="w",compression=self.compression,compresslevel=self.compresslevel) as zip:
            if len(backup_files) == 0:
                zip.write(os.path.join(game.savegame_root,game.savegame_dir),arcname=game.savegame_dir.replace("\\","/"))
            else:
                for i,isdir in backup_files:
                    if (isdir):
                        zip.mkdir('/'.join((game.savegame_dir.replace('\\','/') ,i.replace("\\","/"))))
                    else:
                        zip.write(os.path.join(game.savegame_root,game.savegame_dir,i),
                                  arcname=os.path.join(game.savegame_dir,i).replace('\\','/'))

    def do_restore(self, game, filename):
        if not game.is_valid():
            raise ValueError("\"game\" is not a valid \"sgbackup.game.Game\" instance!")
        
        if not os.path.isfile(filename):
            raise ValueError("\"filename\" does not point to a archive file!")
        
        if not os.path.exists(game.savegame_root):
            os.makedirs(game.savegeame_root)

        with zipfile.ZipFile(filename,mode='r') as zip:
            zip.extractall(game.savegame_root)

    def file_is_archive(self, filename):
        return zipfile.is_zipfile(filename)