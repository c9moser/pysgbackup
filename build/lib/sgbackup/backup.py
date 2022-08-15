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

def delete_backup(game,filename):
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
    
    for k,cb in config.CONFIG['delete-backup-callbacks'].items():
        if cb:
            if config.CONFIG['verbose']:
                print("<sgbackup delete-backup:callback> {}".format(k))
            cb(game,filename)
# delete_backup()

def delete_backups(game,keep_latest=True):
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
        
    for k,cb in config.CONFIG['delete-savegames-callbacks'].items():
        if cb:
            cb(game)
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
                    cb(game,os.path.join(backup_dir,i),os.path.join(backup_dir,fname))
# unfinal

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
        with open(listfile,'a') as lf:
            lf.write('{0}\n'.format(rel_path))
            
    savegames = find_backups(game,reverse=True)
    max_savegames = config.CONFIG['backup.max']
    if max_savegames <= 0:
        return
        
    if len(savegames) > max_savegames:
        for i in savegames[max_savegames:]:
            delete_backup(game,i)
            
    if config.CONFIG['backup-callbacks']:
        for k,cb in config.CONFIG['backup-callbacks'].items():
            if config.CONFIG['verbose']:
                print('<sgbackup backup:callback> {}'.format(k))
            cb(game,backup_file)
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
    
    for k,cb in config.CONFIG['restore-callbacks'].items():
        if cb:
            cb(game,filename)
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
        
def check(game,create_missing=False,check_deleted=False,delete_failed=False,ask=True):
    backup_keys=['/'.join((game.savegame_name,os.path.basename(i))) for i in find_backups(game)]
    verbose= config.CONFIG['verbose']
    with shelve.open(config.CONFIG['backup.checksum-database']) as d:
        for i in backup_keys:
            if verbose:
                print("<checksum:check> {0}".format(i))
            if i in d:
                check = d[i]
                h = hashlib.new(check['algorithm'])
                with open(os.path.normpath(os.path.join(config.CONFIG['backup.dir'],i)),'rb') as ifile:
                    h.update(ifile.read())
                digest = h.hexdigest()
                
                if (check['hash'] == digest):   
                    print('<checksum:{0}:{1}> OK'.format(check['algorithm'],i))
                else:
                    print('<checksum:{0}:{1}> FAILED'.format(check['algorithm'],i))
                    filename = os.path.normpath(os.path.join(config.CONFIG['backup.dir'],i))
                    if (ask):
                        ask = input('Delete SaveGame? [Y/N] ')
                        if (ask.upper() == 'Y'):
                            if (config.CONFIG['verbose']):
                                print('<delete> {0}'.format(filename))
                            os.unlink(filename)
                    elif delete_failed:
                        if (config.CONFIG['verbose']):
                            print('<delete> {0}'.format(filename))
                        os.unlink(filename)
            elif create_missing and config.CONFIG['backup.checksum'] != 'None':
                print('<checksum:{0}:create> {1}'.format(config.CONFIG['backup.checksum'],i))
                cksum=config.CONFIG['backup.checksum']
                h = hashlib.new(cksum)
                with open(os.path.normpath(os.path.join(config.CONFIG['backup.dir'],i)),'rb') as ifile:
                    h.update(ifile.read())
                digest = h.hexdigest()
                d[i] = {'algorithm': cksum, 'hash': digest}
            elif verbose:
                print('<checksum> No checksum for "{0}"!'.format(i))
                

        if (check_deleted):
            check_key='/'.join((game.savegame_name,game.savegame_name + '.'))
            
            for k in d.keys():
                if k.startswith(check_key):
                    if not os.path.isfile(os.path.normpath(os.path.join(config.CONFIG['backup.dir'],k))):
                        if verbose:
                            print('<checksum:delete> {0}'.format(k))
                        del d[k]
# check()

