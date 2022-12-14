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
import glob

def find_latest_backup(game):
    sgdir = os.path.join(config.CONFIG['backup.dir'],game.savegame_name)
    latest  = ""
    if os.path.isdir(sgdir):
        archiver=archivers.get_archiver()
        filename = os.path.join(sgdir,'.'.join((game.savegame_name,'final',archiver.extension)))
        if os.path.isfile(filename):
            return filename
        
        for ext in config.CONFIG['archivers'].keys():
            filename = os.path.join(sgdir,'.'.join((game.savegame_name,'final',ext)))
            if os.path.isfile(filename):
                return filename
                    
        latest_ctime = 0
        for i in sorted(os.listdir(sgdir),reverse=True):
            for ext in config.CONFIG['archivers'].keys():
                if fnmatch.fnmatch(i,'.'.join((game.savegame_name,'*',ext))):
                    filename = os.path.join(sgdir,i)
                    stat = os.stat(filename)
                    if stat.st_ctime > latest_ctime:
                        latest = filename
                        latest_ctime = stat.st_ctime
    return latest
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

def find_all_final_backups(game):
    sgdir = os.path.join(config.CONFIG['backup.dir'],game.savegame_name)
    backups = []
    for ext in config.CONFIG['archivers'].keys():
        fname = os.path.join(sgdir,'{0}.final.{1}'.format(game.savegame_name,ext))
        if os.path.isfile(fname):
            backups.append(fname)
            
        for f in glob.glob(os.path.join(sgdir,'{0}.final.*.{1}'.format(game.savegame_name,ext))):
            backups.append(f)
            
    return sorted(backups)
# find_all_final_backups()

def delete_backup(db,game,filename):
    if os.path.isabs(filename):
        fn = filename
    else:
        fn = os.path.join(config.CONFIG['backup.dir'],game.savegame_name,os.path.basename(filename))
    
    db.delete_game_backup(game,fn)
    
    if os.path.isfile(fn):
        if config.CONFIG['verbose']:
            print('[delete] {0}'.format(fn))
        os.unlink(fn)
    
    for k,cb in config.CONFIG['delete-backup-callbacks'].items():
        if cb:
            if config.CONFIG['verbose']:
                print("<sgbackup delete-backup:callback> {}".format(k))
            cb(db,game,fn)
# delete_backup()

def delete_backups(db,game,keep_latest=True):
    latest = find_latest_backup(game)
    for i in find_backups(game):
        if keep_latest and i == latest:
            continue
            
        ignore_file = False
        for ext in config.CONFIG['archivers']:
            if fnmatch.fnmatch(os.path.basename(i),"{0}.latest.*.{1}".format(game.savegame_name,ext)):
                ingore_file = True
                break
        if ignore_file:
            continue
        
        delete_backup(db,game,i)
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
        
    for k,cb in config.CONFIG['delete-savegames-callbacks'].items():
        if cb:
            cb(db,game)
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

def unfinal(db,game):
    game.final_backup=False
    db.add_game(game)
    
    backup_dir=os.path.join(config.CONFIG['backup.dir'],game.savegame_name)
    #get final max
    globs = ["{0}.final.*.{1}".format(game.savegame_name,i) for i in config.CONFIG['archivers'].keys()]
    globs = tuple(globs)
    sglen=len(game.savegame_name + '.final.')
    cnt=-1
    for i in globs:
        for j in glob.glob(i,root_dir=backup_dir):
            try:
              num = int(j[sglen:].split('.')[0])
              if num > cnt:
                cnt=num
            except Exception as ex:
                continue

    cnt += 1
    globs = ["{0}.final.{1}".format(game.savegame_name,i) for i in config.CONFIG['archivers'].keys()]
    
    for i in globs:
        for j in glob.glob(i,root_dir=backup_dir):
            fname = "{0}.final.{1}.{2}".format(game.savegame_name,cnt,j[sglen:])
            chk_old = "{0}/{1}".format(game.savegame_name,j)
            chk_new = "{0}/{1}".format(game.savegame_name,fname)
        
            os.rename(os.path.join(backup_dir,j),os.path.join(backup_dir,fname))
            if config.CONFIG['backup.write-listfile']:
                with open(config.CONFIG['backup.listfile'],'a') as ofile:
                    ofile.write(chk_new + '\n')
        
            with shelve.open(config.CONFIG['backup.checksum-database']) as d:
                d[chk_new] = d[chk_old]
                del d[chk_old]
            
            for k,cb in config.CONFIG['rename-backup-callbacks']:
                if cb:
                    cb(db,game,os.path.join(backup_dir,i),os.path.join(backup_dir,fname))
# unfinal

def backup(db,game):
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
        
        h = hashlib.new(cksum)    
        with open(backup_file,'rb') as bf:
            h.update(bf.read())
        digest = h.hexdigest()
        
        db.add_game_backup(game,backup_file,cksum,digest)
            
    savegames = find_backups(game,reverse=True)
    max_savegames = config.CONFIG['backup.max']
    if max_savegames <= 0:
        return
        
    count = 0
    if len(savegames) > max_savegames:
        for i in savegames:
            f = os.path.basename(i)
            if fnmatch.fnmatch(f,'{}.final.*'.format(game.savegame_name)):
                continue
                
            count += 1
            if count > max_savegames:
                delete_backup(db,game,i)
            
    if config.CONFIG['backup-callbacks']:
        for k,cb in config.CONFIG['backup-callbacks'].items():
            if config.CONFIG['verbose']:
                print('<sgbackup backup:callback> {}'.format(k))
            cb(db,game,backup_file)
# backup()

def backup_all(db,include_final=False):
    for i in db.list_game_ids():
        game = db.get_game(i)
        if not game.final_backup or include_final:
            backup(db,game)
# backup_all()          

def get_archiver_for_file(filename):
    archiver = archivers.get_archiver()
    for i in archiver.known_extensions:
        if filename.endswith('.' + i):
            return archiver
            
    for i in config.CONFIG['archivers'].keys():
        if filename.endswith('.' + i):
            return archivers.get_archiver(config.CONFIG['archivers'][i]['archiver'])        

                
def restore(db,game,filename):
    archiver = get_archiver_for_file(filename)
    archiver.restore(filename,game.savegame_root)
    
    for k,cb in config.CONFIG['restore-callbacks'].items():
        if cb:
            cb(game,filename)
# restore()

def restore_ask(db,game):
    d = {}
    count = 0
    for i in find_backups(game,reverse=True):
        count += 1
        fn = os.path.basename(i)
        timestamp = fn[len(game.savegame_name) + 1:]
        timestamp = timestamp.split('.')[0]
        if (timestamp == 'final'):
            try:
                final_count = fn[len(game.savegame_name + ".final.")]
                final_count = int(final_count.split('.')[0])
                d[count] = {'timestamp': 'final.{0}'.format(final_count),'file':i}
            except Exception:
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

    restore(db,game,d[x]['file'])

    
def restore_all(db):
    for game_id in db.list_game_ids():
        game = db.get_game(game_id)
        
        bdir = os.path.join(config.CONFIG['backup.dir'], game.savegame_name)
        if not os.path.isdir(bdir):
            continue
            
        filename = find_latest_backup(game)
        if filename:
            restore(db,game,filename)
# restore_all()
        
def check(db,game,create_missing=False,check_deleted=False,delete_failed=False):
    backup_files= find_backups(game)
    verbose= config.CONFIG['verbose']
                
    if check_deleted:
        for fdata in db.get_game_backups(game):
            fn = os.path.join(config.CONFIG['backup.dir'],game.savegame_name,fdata['filename'])
            if not os.path.isfile(fn):
                delete_backup(db,game,fn)
                
    for fn in backup_files:
        backup = db.get_game_backup(game,fn)
        if backup:
            print("[sgbackup check:{}] {} ... ".format(backup['checksum'],fn), end='')
            h = hashlib.new(backup['checksum'])
            with open(fn,'rb') as ifile:
                h.update(ifile.read())
            if h.hexdigest() == backup['hash']:
                print('OK')
            else:
                print('FAILED')
                if delete_failed:
                    delete_backup(db,game,fn)
        elif create_missing:
            cksum = config.CONFIG['backup.checksum']
            print("[sgbackup check(create):{}] {}".format(cksum,fn))
            h = hashlib.new(cksum)
            with open(fn,'rb') as ifile:
                h.update(ifile.read())
            db.add_game_backup(game,fn,cksum,h.hexdigest())
# check()

def check_backup(db,game,backup):
    if os.path.isabs(backup):
        f = backup
    else:
        f = os.path.join(CONFIG['backup.dir'],game.savegame_name,f)
    
    if not os.path.isfile(f):
        return False
            
    db_backup = db.get_game_backup(game,os.path.basename(f))
    if not db_backup:
        return False
    
        
    h = hashlib.new(db_backup['checksum'])
    with open(f,'rb') as ifile:
        h.update(ifile.read())
        
    return (h.hexdigest() == db_backup['hash'])
# check_backup

