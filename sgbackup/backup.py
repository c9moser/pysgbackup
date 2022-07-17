#-*- coding: utf-8 -*-

from . import config,archivers
import os
import datetime
import sys

def get_backup_filename(game,archiver=None):
    if not archiver:
        archiver=archivers.get_archiver()
        
    if game.final_backup:
        fname='.'.join((game.savegame_name,'final',archiver.extension))
    else:
        dt=datetime.datetime.now()
        date_str=dt.strftime("%Y%m%d-%H%M%S")
        fname='.'.join((game.savegame_name,date_str,archiver.extension))
        
    return os.path.join(config.CONFIG['backup.dir'],,game.savegame_name,fname)
# get_backup_filename()

def backup(game,listfile=None,write_listfile=False):
    archiver=archivers.get_archiver()
    backup_file=get_backup_filename(game,archiver)
    backup_dir=os.path.dirname(backup_file)
    if not os.path.exists(os.path.join(game.savegame_root,game.savegame_dir)):
        if config.CONFIG['verbose']:
            print("Unable to backup '{0}'! (No such file or directory!)".format(os.path.join(game.savegame_root,game.savegame_dir)))
        return    
    
    print ("[sgbackup backup] {0}".format(game.name))
        
    if not os.path.exists(backup_dir):
        if config.CONFIG['verbose']:
            print('mkdir: {0}'.format(backup_dir))
        os.makedirs(backup_dir)        
    archiver.backup(backup_file,game.savegame_root,game.savegame_dir)
    
    if not os.path.isfile(backup_file):
        print('Backup failed!',file=sys.stderr)
        exit(3)
        
    checksum = config.CONFIG['backup.checksum.values'][config.CONFIG['backup.checksum']](backup_file)
    if checksum:
        csid = config.CONFIG['backup.checksum']
        if config.CONFIG['verbose']:
            print("checksum {0}: {1}".format(csid,backup_file))
        csfile = '.'.join((backup_file,csid))
        with open(csfile,'w') as csf:
            csf.write('{0} ({1}) = {2}\n'.format(csid,os.path.basename(backup_file),checksum))
            
    if write_listfile:
        if not listfile:
            listfile=config.CONFIG['backup.listfile']
            
        rel_path=os.path.join(game.savegame_name,os.path.basename(backup_file))
        with open(listfile,'a'):
            write('{0}\n'.format(rel_path))    
# backup()

def backup_all(db,listfile=None,write_listfile=False,include_final=False):
    for i in db.list_game_ids():
        game = db.get_game(i)
        if not game.final_backup or include_final:
            backup(game,listfile,write_listfile)
# backup_all()          


