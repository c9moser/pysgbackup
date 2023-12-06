import subprocess
import os
from .settings import PLUGIN_ID,CHECKSUMS
import shlex

def create_checksums(app,game,filename):
    sect = PLUGIN_ID
    cwd = os.getcwd()
    os.chdir(os.path.dirname(filename))

    for csum in app.config.get_string_list(sect,'checksums'):
        csum_cmd = app.config.get_string(sect,csum)
        if not csum_cmd:
            continue
        command = [csum_cmd] + shlex.split(app.config.get_string(sect,'checksum_create_flags')) + [os.path.basename(filename)]
        proc = subprocess.run(command,capture_output=True)
        if proc.returncode == 0:
            csum_file = '.'.join((filename,csum))
            with open(os.path.basename(csum_file),'wb') as ofile:
                ofile.write(proc.stdout)
            if app.config.verbose:
                print("[{checksum}] {file} created".format(checksum=csum,file=csum_file))
            app.archivers.backup_file(game,csum_file)

    os.chdir(cwd)

def create_missing_checksums(app):
    sect = PLUGIN_ID
    cwd = os.getcwd()
    for game in app.games.games:
        if not os.path.isdir(game.backup_dir):
            continue
        os.chdir(game.backup_dir)
        for backup in game.backups:
            for csum in app.config.get_string_list(sect,'checksums'):
                csum_file = '.'.join((backup,csum))
                if os.path.isfile(csum_file):
                    continue
                csum_cmd = app.config.get_string(sect,csum)
                csum_flags = app.config.get(sect,'checksum_create_flags')
                if not csum_cmd:
                    continue
                command = [csum_cmd] + shlex.split(csum_flags) + [os.path.basename(backup)]
                
                proc = subprocess.run(command,capture_output=True)
                
                if proc.returncode == 0:    
                    with open(os.path.basename(csum_file),'wb') as ofile:
                        ofile.write(proc.stdout)
                    if app.config.verbose:
                        print("[{checksum}] {file} created".format(checksum=csum,file=csum_file))
                    app.archivers.backup_file(game,csum_file)
                else:
                    print(proc.stdout.decode('utf-8'))
    os.chdir(cwd)

def check_checksums(app,backup_file):
    cwd = os.getcwd()
    os.chdir(os.path.dirname(backup_file))
    ret = True
    for csum in CHECKSUMS:
        csum_file = '.'.join((backup_file,csum))
        if os.path.isfile(csum_file):
            csum_cmd =  app.config.get_string(PLUGIN_ID,csum)
            csum_flags = app.config.get_string(PLUGIN_ID,'checksum_check_flags')
            if not csum_cmd or not csum_flags:
                continue
            command = [csum_cmd] + shlex.split(csum_flags) + [os.path.basename(csum_file)]
            proc = subprocess.run(command,capture_output=True)
            print ("[{checksum}] {file} ... ".format(checksum=csum,file=os.path.basename(backup_file)),
                   end="")
            if proc.returncode == 0:
                print("OK")
            else:
                print("FAILED")
                ret = False
    os.chdir(cwd)
    return ret

def check_checksums_for_game(app,game,success_callback=None,failed_callback=None):
    """! @brief check checksums for game
       @arg app Application instance
       @arg game Game instancse
       @arg success_callback Callback if checksumming of a file is a success. 
       callback(app,game,file)
       @arg failed_callback Callback function if checksumming of a file fails. 
       callback(app,game,file)
    """
    if not os.path.isdir(game.backup_dir):
        return
    
    backups = game.backups
    if not backups:
        return
    
    for bf in backups:
        if check_checksums(app,bf):
            if callable(success_callback):
                success_callback(app,game,bf)
        else:
            if callable(failed_callback):
                failed_callback(app,game,bf)

def check_all_checksums(app,success_callback=None,failed_callback=None):
    """! @brief Check checksums for all backups.
        @arg app Application instance.
        @arg success_callback callback function if checksumming of a file is a success.
        callback(app,game,file)
        @arg failed_callback callback function if checksumming of a file failed.
        callback(app,game,file)
    """
    for game in app.games.games:
        if app.config.verbose:
            print("[CHECKSUM] {game}".format(game=game.game_name))
        check_checksums_for_game(app,game,success_callback=success_callback,failed_callback=failed_callback)
