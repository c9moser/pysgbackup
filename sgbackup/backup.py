#-*- coding: utf-8 -*-

from . import config,archivers
import os
import datetime
import sys
import fnmatch
import shelve
import pickle
import hashlib
import pathlib

def find_latest_backup(game):
    sgdir = os.path.join(config.CONFIG['backup.dir'],game.savegame_name)
    if os.path.isdir(sgdir):
        archiver=archivers.get_archiver()
        filename = os.path.join(sgdir,'.'.join((game.savegame_name,'final',archiver.extension)))
        if os.path.isfile(filename):
            return filename
        
        for ext in config.CONFIG['archivers'].keys():
            filename = os.path.join(sgdir,'.'.join((game.savegame_name,'final',ext)))
            if os.path.isfile(filename):
                return filename
                    
        for i in sorted(os.listdir(sgdir),reverse=True):
            for ext in config.CONFIG['archivers'].keys():
                if fnmatch.fnmatch(i,'.'.join((game.savegame_name,'*',ext))):
                    return os.path.join(sgdir,i)
    return ""
# find_latest_savegame()

def find_backups(game,reverse=False):
    sgdir = os.path.join(config.CONFIG['backup.dir'],game.savegame_name)
    ret=[]
    if os.path.isdir(sgdir):
        for i in sorted(os.listdir(sgdir),reverse=reverse):
            for ext in config.CONFIG['archivers'].keys():
                if fnmatch.fnmatch(i,'.'.join((game.savegame_name,'*',ext))):
                    ret.append(os.path.join(sgdir,i))
    return ret
# find_savegames()

def delete_backup(game,filename):
    def _get_checksum_file(filename):
        checksum_ext = ['b2','md5','sha1','sha224','sha256','sha384','sha512']
        for ext in checksum_ext:
            cfile = '.'.join((filename,ext))
            if os.path.isfile(cfile):
                return cfile
                
        return ""
    # _get_checksum_file()
    
    cfile = _get_checksum_file(filename)
    if cfile:
        if config.CONFIG['verbose']:
            print('[delete] {0}'.format(cfile))    
        os.unlink(cfile)
    if os.path.isfile(config.CONFIG['backup.checksum-database']):
        with shelve.open(config.CONFIG['backup.checksum-database']) as d:
            key = '/'.join((game.savegame_name,os.path.basename(filename)))
            if key in d:
                if config.CONFIG['verbose']:
                    print('[delete checksum] {0}',key)
                del d[key]
    
    if config.CONFIG['verbose']:
        print('[delete] {0}'.format(filename))
    os.unlink(filename)
# delete_savegame()

def delete_backups(game,keep_latest=True):
    latest = find_latest_backup(game)
    for i in find_backups(game):
        if keep_latest and i == latest:
            continue
        delete_backup(game,i)
# delete_savegames()

def delete_savegames(game):
    def _rmdir(directory):
        directory = pathlib.Path(directory)
        for item in directory.iterdir():
            if item.is_dir():
                _rmdir(item)
            else:
                if config.CONFIG['verbose']:
                    print('<delete> {0}'.format(item.as_posix()))
                item.unlink()
        if config.CONFIG['verbose']:
            print("<delete> {0}/".format(item.as_posix()))
        directory.rmdir()
    # _rmdir()
    
    sgdir=os.path.join(game.savegame_root,game.savegame_dir)
    if os.path.isdir(sgdir):
        for i in os.listdir(sgdir):
            if i == '.' or i == '..':
                continue
                
            path = os.path.join(sgdir,i)
            if os.path.isdir(path):         
                _rmdir(path)
            elif os.path.isfile(path):
                if config.CONFIG['verbose']:
                    print("<delete> {0}".format(path))
                os.unlink(path)
    elif os.path.isfile(sgdir):
        os.unlink(sgdir)
# delete_savegames()

def get_backup_filename(game,archiver=None):
    if not archiver:
        archiver=archivers.get_archiver()
        
    if game.final_backup:
        fname='.'.join((game.savegame_name,'final',archiver.extension))
    else:
        dt=datetime.datetime.now()
        date_str=dt.strftime("%Y%m%d-%H%M%S")
        fname='.'.join((game.savegame_name,date_str,archiver.extension))
        
    return os.path.join(config.CONFIG['backup.dir'],game.savegame_name,fname)
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
        
    # add checksum to database
    if config.CONFIG['backup.checksum'] != 'None':
        cksum = config.CONFIG['backup.checksum']
        key = '/'.join((game.savegame_name,os.path.basename(backup_file)))
        
        if config.CONFIG['verbose']:
            print("<checksum:{0}> {1}".format(cksum,key))
            
        with shelve.open(config.CONFIG['backup.checksum-database']) as d:
            h = hashlib.new(cksum)
            with open(backup_file,'rb') as bf:
                h.update(bf.read())
            d[key] = {
                'algorithm': cksum,
                'hash': h.hexdigest()
            }
            
    if write_listfile:
        if not listfile:
            listfile=config.CONFIG['backup.listfile']
            
        rel_path=os.path.join(game.savegame_name,os.path.basename(backup_file))
        with open(listfile,'a'):
            write('{0}\n'.format(rel_path))
            
    savegames = find_backups(game,reverse=True)
    max_savegames = config.CONFIG['backup.max']
    if max_savegames <= 0:
        return
        
    if len(savegames) > max_savegames:
        for i in savegames[max_savegames:]:
            delete_backup(game,i)
# backup()

def backup_all(db,listfile=None,write_listfile=False,include_final=False):
    for i in db.list_game_ids():
        game = db.get_game(i)
        if not game.final_backup or include_final:
            backup(game,listfile,write_listfile)
# backup_all()          

def get_archiver_for_file(filename):
    archiver = archivers.get_archiver()
    for i in archiver.known_extensions:
        if filename.endswith('.' + i):
            return archiver
            
    for i in config.CONFIG['archivers'].keys():
        if filename.endswith('.' + i):
            return archivers.get_archiver(config.CONFIG['archivers'][i]['archiver'])        

                
def restore(game,filename):
    archiver = get_archiver_for_file(filename)
    archiver.restore(filename,game.savegame_root)
# restore()

def restore_ask(game):
    d = {}
    count = 0
    for i in find_backups(game,reverse=True):
        count += 1
        fn = os.path.basename(i)
        timestamp = fn[len(game.savegame_name) + 1:]
        timestamp = timestamp.split('.')[0]
        if (timestamp == 'final'):
            d[count] = {'timestamp': timestamp,'file':i}
        else:
            dt = datetime.datetime.strptime(timestamp,'%Y%m%d-%H%M%S')
            d[count] = {'timestamp':dt.strftime('%c'),'file':i}
    
    for k in sorted(d.keys()):
        print('{0}\t{1}'.format(k,d[k]['timestamp']))
    
    valid_input = False
    while not valid_input:
        x0 = input("Please enter SaveGame number to restore or q to quit: ")
        if (x0.lower() == 'q'):
            return
        try:
            x = int(x0)
            if x in d:
                valid_input=True
        except Exception:
            print ("'{0}' is not a valid input!".format(x0))

    restore(game,d[x]['file'])

    
def restore_all(db):
    for game_id in db.list_game_ids():
        game = db.get_game(game_id)
        
        bdir = os.path.join(config.CONFIG['backup.dir'], game.game_id)
        if not os.path.isdir(bdir):
            continue
            
        filename = find_latest_savegame(game)
        if filename:
            restore(game,filename)
# restore_all()
        
    

