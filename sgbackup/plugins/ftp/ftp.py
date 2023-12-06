import os
import sys
from ftplib import FTP,FTP_TLS

from gi.repository import GObject
from .error import FtpConnectionError
import sgbackup
class FtpClient(GObject.GObject):
    __name__ = "sgbackup-plugin-ftp-Ftp"
    __gsignals__ = {
        'destroy': (GObject.SIGNAL_RUN_LAST,None,())
    }

    def __init__(self,app,
                 id=-1,
                 host="localhost",
                 port=21,
                 user="anonymous",
                 password="",
                 use_tls=False,
                 backup_dir="",
                 auto_backup=False,
                 timeout=300):
        GObject.GObject.__init__(self)
        self.__app = app
        self.__id = self.sanitize_id(id)
        self.__host = host
        self.__port = port
        self.__user = user
        self.__password = password
        self.__use_tls = use_tls
        self.__backup_dir = backup_dir
        self.__auto_backup = auto_backup
        self.__timeout = timeout

        self.__ftp = None

        self.__archivermanager_backup_slot='_plugin_ftp_ftpclient{}_backup_slot'.format(str(self.id))
        self.__archivermanager_backup_file_slot='_plugin_ftp_ftpclient{}_backup_file_slot'.format(str(self.id))
                                                                                                  
        if self.auto_backup:
            archivers = self.application.archivers
            setattr(archivers,self.__archivermanager_backup_slot,archivers.connect('backup',self.__on_backup))
            setattr(archivers,self.__archivermanager_backup_file_slot,archivers.connect('backup-file',self.__on_backup_file))
            
    @staticmethod
    def new_from_config(app,id:int,group:str):
        cfg = app.config
        kwargs = {}
        
        if cfg.has_key(group,"host"):
            kwargs['host'] = cfg.get_string(group,"host")
        if cfg.has_key(group,"port"):
            kwargs['port'] = cfg.get_integer(group,"port")
        if cfg.has_key(group,"user"):
            kwargs['user'] = cfg.get_string(group,"user")
        if cfg.has_key(group,"password"):
            kwargs['password'] = cfg.get_string(group,"password")
        if cfg.has_key(group,"useTLS"):
            kwargs['use_tls'] = cfg.get_boolean(group,"useTLS")
        if cfg.has_key(group,"backupDir"):
            kwargs['backup_dir'] = cfg.get_string(group,"backupDir")
        if cfg.has_key(group,"autoBackup"):
            kwargs['auto_backup'] = cfg.get_boolean(group,"autoBackup")
        if cfg.has_key(group,'timeout'):
            kwargs['timeout'] = cfg.get_integer(group,"timeout")

        return FtpClient(app,id,**kwargs)
    
    def sanitize_id(self,id):
        if id < 0:
            max = 0
            for ftp_group in sorted(i for i in self.application.config.groups if i.startswith('ftp:')):
                try:
                    x,y = ftp_group.split(':',2)
                    if int(y) > max:
                        max = int(y)
                except:
                    continue
            return (max + 1)
        return id
    
    @GObject.Property
    def application(self):
        return self.__app
    
    @GObject.Property
    def id(self):
        return self.__id
        
    
    @GObject.Property
    def host(self):
        return self.__host
    @host.setter
    def host(self,host):
        self.__host = host
    
    @GObject.Property
    def port(self):
        return self.__port
    @port.setter
    def port(self,port):
        if port > 65535:
            raise ValueError("Port number too high!")
        self.__port = port
      
    @GObject.Property
    def user(self):
        return self.__user
    @user.setter
    def user(self,user):
        self.__user = user

    
    @GObject.Property
    def password(self):
        return "*" * 8
    @password.setter
    def password(self,passwd):
        self.__password = passwd
    
    @GObject.Property
    def use_tls(self):
        return self.__use_tls
    @use_tls.setter
    def use_tls(self,b):
        self.__use_tls = b
    
    @GObject.Property
    def backup_dir(self):
        return self.__backup_dir
    @backup_dir.setter
    def backup_dir(self,dir):
        self.__backup_dir = dir

    @GObject.Property(bool)
    def auto_backup(self):
        return self.__auto_backup
    @auto_backup.setter
    def auto_backup(self,enable:bool):
        enable = bool(enable)
        if enable == self.auto_backup:
            return
        
        archivers=self.application.archivers
        if enable:
            setattr(archivers,self.__archivermanager_backup_slot,archivers.connect('backup',self.__on_backup))
            setattr(archivers,self.__archivermanager_backup_file_slot,archivers.connect('backup-file',self.__on_backup_file))
            self.__auto_backup = True
        else:
            if hasattr(archivers,self.__archivermanager_backup_slot):
                archivers.disconnect(getattr(archivers,self.__archivermanager_backup_slot))
                delattr(archivers,self.__archivermanager_backup_slot)
            if hasattr(archivers,self.__archivermanager_backup_file_slot):
                archivers.disconnect(getattr(archivers,self.__archivermanager_backup_file_slot))
                delattr(archivers,self.__archivermanager_backup_file_slot)
            self.__auto_backup = False

    @GObject.Property
    def timeout(self):
        return self.__timeout
    @timeout.setter
    def timeout(self,timeout):
        self.__timeout = int(timeout)

    def save(self):
        config = self.application.config
        group = "ftp:{}".format(str(self.id))
        config.set_string(group,"host",self.host)
        config.set_integer(group,"port",self.port)
        config.set_string(group,"user",self.user)
        config.set_string(group,"password",self.__password)
        config.set_string(group,"backupDir",self.backup_dir)
        config.set_boolean(group,"useTLS",self.use_tls)
        config.set_boolean(group,"autoBackup",self.auto_backup)
        config.set_integer(group,"timeout",self.timeout)
        config.save()

    def ftp_connect(self):
        if self.__ftp is None:
            if self.use_tls:
                ftp = FTP_TLS(timeout=self.timeout)
            else:
                ftp = FTP(timeout=self.timeout)
            try:
                ftp.connect(self.host,self.port)
                if self.use_tls:
                    try:
                        ftp.auth()
                    except:
                        pass

                    try:
                        ftp.prot_p()
                    except:
                        pass
                ftp.login(self.user,self.__password)
                self.__ftp = ftp
                return True
            except:
                return False
            
        self.__ftp.close()
        try:
            self.__ftp.connect(self.host,self.port)
            if self.use_tls:
                try:
                    self.__ftp.auth()
                except:
                    pass
                try:
                    self.__ftp.prot_p()
                except:
                    pass
            self.__ftp.login(self.user,self.__password)
            return True
        except:
            self.close()
        return False
        
    def close(self):
        if self.__ftp is not None:
            self.__ftp.close()
            self.__ftp = None

    def create_backupdir(self):
        if self.backup_dir:
            if self.backup_dir == ".":
                return
            
        if self.backup_dir.startswith('/'):
            isabs = True
        else:
            isabs = False

        ftp_wd = self.__ftp.pwd()

        if isabs:
            pv = self.backupdir[1:].split('/')
            self.__ftp.cwd('/')
        else:
            pv = self.backupdir.split('/')

        for i in pv:
            try:
                self.__ftp.cwd(i)
            except:
                try:
                    self.__ftp.mkd(i)
                    self.__ftp.cwd(i)
                except Exception as err:
                    self.cwd(ftp_wd)
                    raise err
        self.cwd(ftp_wd)

    def synchronize(self):
        def synchronize_subdir(backup_dir,subdir,ftp_subdir):
            if not os.path.isdir(os.path.join(backup_dir,subdir)):
                return
            
            ftp_wd = self.__ftp.pwd()

            try:
                self.__ftp.cwd(ftp_subdir)
            except:
                try:
                    self.__ftp.mkd(ftp_subdir)
                    self.__ftp.cwd(ftp_subdir)
                except Exception as error:
                    print(error,file=sys.stderr)
                    self.cwd(ftp_wd)
                    return


            for i in os.listdir(os.path.join(backup_dir,subdir)):
                fname = os.path.join(backup_dir,subdir,i)
                if os.path.isdir(fname):
                    synchronize_subdir(backup_dir,os.path.join(subdir,i),i)
                else:
                    print("[FTP put] {} ...".format(fname),end=" ")
                    with open(fname,'rb') as ifile:
                        try:
                            self.__ftp.storbinary("STOR {}".format(i),ifile,blocksize=2048)
                            print("OK")
                        except:
                            print("FAILED")

            self.__ftp.cwd(ftp_wd)
                            
            
        close_connection = False
        if not self.__ftp:
            if not self.ftp_connect():
                raise FtpConnectionError("Unable to connect to host \"{host}\"!".format(host=self.host))
            self.close_connection = True

        ftp_wd = self.__ftp.pwd()
        try:
            self.__ftp.cwd(self.backup_dir)
        except:
            try:
                self.create_backupdir()
                self.__ftp.cwd(self.backupdir)

            except Exception as err:
                self.__ftp.cwd(ftp_wd)
                if close_connection:
                    self.close()
                    raise err

        ftp_bd = self.__ftp.pwd()

        for game in self.application.games.games:
            bd = game.backup_dir
            if not os.path.isdir(game.backup_dir):
                continue

            try:
                self.__ftp.cwd(game.savegame_name)
            except:
                try:
                    self.__ftp.mkd(game.savegame_name)
                    self.__ftp.cwd(game.savegame_name)
                except Exception as err:
                    self.cwd(ftp_wd)
                    if self.close_connection:
                        self.close()
                    raise err
                
            try:
                bd_list = os.listdir(bd)
            except:
                self.__ftp.cwd(ftp_bd)
                continue

            
            for lfn,rfn in ((os.path.join(bd,i),i) for i in bd_list):
                if os.path.isdir(os.path.join()):
                    synchronize_subdir(bd,rfn,rfn)                    
                else:
                    print("FTP put: {} ".format(rfn),end="... ")
                    with open(lfn,'rb') as ifile:
                        try:
                            self.__ftp.storbinary("STOR {}".format(rfn),ifile)
                            print("OK")
                        except Exception as err:
                            print("FAILED")
                            self.cwd(ftp_wd)

            self.__ftp.cwd(ftp_bd)
        self.__ftp.cwd(ftp_wd)
        if close_connection:
            self.close()

    def destroy(self):
        self.emit('destroy')

    def do_destroy(self):
        archivers = self.application.archviers
        if hasattr(archivers,self.__archivermanager_backup_slot):
            archivers.disconnect(getattr(archivers,self.__archivermanager_backup_slot))
            delattr(archivers,self.__archivermanager_backup_slot)

        if hasattr(archivers,self.__archivermanager_backup_file_slot):
            archivers.disconnect(getattr(archivers,self.__archivermanager_backup_file_slot))
            delattr(archivers,self.__archivermanager_backup_file_slot)

        self.__app = None

    def _rcd_to_game_dir(self,gamedir):
        wd = self.__ftp.pwd()

        if gamedir.startswith('/'):
            isabs = True
        else:
            isabs = False

        if isabs:
            self.__ftp.cwd("/")
            pv = os.path.split(gamedir[1:])
        else:
            pv = os.path.split(gamedir)

        for i in pv:
            try:
                self.__ftp.cwd(i)
            except:
                try:
                    self.__ftp.mkd(i)
                    self.__ftp.cwd(i)
                except Exception as err:
                    self.__ftp.cwd(wd)
                    raise err
        return wd

    def fetch_all_game(self,game):
        def fetch_dir(game,ftp_game_dir,subdir=None):
            def list_cb(entries,line):
                entry = line.split(None,9)
                if len(entry) == 9:
                    entries.append(entry)

            if subdir:
                ftp_wd = self.__ftp.pwd()
                try:
                    self.__ftp.cwd(os.path.join(ftp_game_dir,subdir))
                except:
                    self.__ftp.cwd(os.path.join(ftp_wd))
                    return

                game_dir = os.path.join(game.backup_dir,subdir)
            else:
                ftp_wd = None
                game_dir = game.backup_dir


            if not os.path.exists(game_dir):
                os.makedirs(game_dir)

            dir_entries = []
            self.__ftp.retrlines("LIST",lambda x: list_cb(dir_entries,x))

            for i in dir_entries:
                if i[0].startswith('d'):
                    if subdir:
                        fetch_dir(game,ftp_game_dir,'/'.join((subdir,i[8])))
                    else:
                        fetch_dir(game,ftp_game_dir,i[8])

                else:
                    #TODO
                    print("fetch file {}".format(i[8]))

            if ftp_wd is not None:
                self.__ftp.cwd(ftp_wd)
                    

        close_connection = False
        if not self.__ftp:
            if not self.ftp_connect():
                print("Unable tp connect to host \"{host}\"!".format(host=self.host),file=sys.stderr)
                return False
            close_connection = True

        gamedir = "/".join((self.backup_dir,game.savegame_name))
        rwd = self.__ftp.pwd()

        try:
            self._rcd_to_game_dir(gamedir)
        except:
            try:
                self.__ftp.cwd(rwd)
            except:
                pass
            if self.close_connection:
                self.close()
            return
        
        fetch_dir(game,gamedir,None)

        try:
            self.__ftp.cwd(rwd)
        except:
            pass

        if close_connection:
            self.close()


    def fetch_all(self):
        for game in self.application.games.games:
            self.fetch_all_game(game)

    def __on_backup(self,archivermanager,archiver,game,file):
        close_connection = False
        if not self.__ftp:
            if not self.ftp_connect():
                print("Unable to connect to host \"{host}\"!".format(host=self.host),files=sys.stderr)
                return
            close_connection = True
        
        gamedir = "/".join((self.backup_dir,game.savegame_name))
        rwd = self.__ftp.pwd()
        try:
            wd = self._rcd_to_game_dir(gamedir)
        except Exception as err:
            try:
                self.__ftp.cwd(rwd)
            except:
                pass

            print("Unable to create and rcd to Game directory! ({message})".format(message=err),file=sys.stderr)
            if close_connection:
                self.close()
            return
        
        if self.application.config.verbose:
            print("[FTP:put] {file}".format(file=file))
        try:
            with open(file,"rb") as ifile:
                self.__ftp.storbinary("STOR {}".format(os.path.basename(file)),ifile)
        except Exception as err:
            print("Uploading file {file} failed! ({message})".format(file=os.path.basename(file),message=err),file=sys.stderr)
        try:
            self.__ftp.cwd(wd)
        except:
            pass

        self.__ftp.cwd(rwd)
        if close_connection:
            self.close()


    def __on_backup_file(self,archivermanager,game,file):
        close_connection = False
        if self.__ftp is None:
            if not self.ftp_connect():
                print("Unable to connect to host \"{host}\"!".format(host=self.host))
                return
            close_connection  = True 
        gamedir = "/".join((self.backup_dir,game.savegame_name))
        rwd = self.__ftp.pwd()

        try:
            wd = self._rcd_to_game_dir(gamedir)
        except Exception as err:
            print("Unable to create and rcd to Game directory! ({message})".format(message=err),file=sys.stderr)
            try:
                self.__ftp.cwd(rwd)
            except:
                pass

            if close_connection:
                self.close()
            return
        
        if self.application.config.verbose:
            print("[FTP:put] {file}".format(file=file))
        try:
            with open(file,"rb") as ifile:
                self.__ftp.storbinary("STOR {}".format(os.path.basename(file)),ifile)
        except Exception as err:
            print("Uploading file {file} failed! ({message})".format(file=os.path.basename(file),message=err),file=sys.stderr)
        try:
            self.__ftp.cwd(rwd)
        except:
            pass
        if close_connection:
            self.close()

class FtpManager(object):
    __name__ = "sgbackup-plugin-ftp-FtpManager"
    __gsignals__ = {
        'destroy': (GObject.SIGNAL_RUN_LAST,None,())
    }

    def __init__(self,app):
        object.__init__(self)
        self.__app = app
        self.__clients={}

    @GObject.Property
    def application(self):
        return self.__app

    @GObject.Property
    def clients(self):
        return self.__clients        

    def add(self,ftpclient):
        if ftpclient.id in self.__clients:
            if self.__clients[ftpclient.id] == ftpclient:
                return
            self.remove(ftpclient.id)
            del self.__clients[ftpclient.id]

        self.__clients[ftpclient.id] = ftpclient

    def get(self,ftpid):
        try:
            return self.__clients[ftpid]
        except:
            raise LookupError("No FTP client with ID {id} found!".format(id=ftpid))

    def remove(self,ftpid):
        if ftpid in self.__clients:
            cli = self.clients[ftpid]
            cli.close()
            cli.destroy()
            del self.clients[ftpid]

    def enable(self):
        for i in sorted(self.application.config.groups):
            if i.startswith("ftp:"):
                try:
                    module,id = i.split(":",2)
                    ftpid = int(id)
                except:
                    continue

                ftpclient = FtpClient.new_from_config(self.application,ftpid,i)
                self.add(ftpclient)
                
                
    def do_destroy(self):
        for cli in self.__clients:
            cli.destroy()
        self.__clients = {}
        self.__app = None
