from sgbackup.command import CommandOptions,Command
from sgbackup.error import OptionError
import getopt
import getpass
from .ftp import FtpClient
import sys

def _print_ftp_list(plugin):
    id_len = 0
    host_len=0
    port_len=0
    for id,client in plugin.ftp.clients.items():
        if len(str(id)) > id_len:
            id_len = len(str(id))
        if len(client.host) > host_len:
            host_len = len(client.host)
        if len(str(client.port)) > port_len:
            port_len = len(str(client.port))

    id_len = ((id_len // 4) + 1) * 4
    host_len = ((host_len // 4) + 1) * 4
    port_len = ((port_len // 4) + 1) * 4

    for id in sorted(plugin.ftp.clients.keys()):
        client=plugin.ftp.clients[id]
        print("{}{}{}{}{}{}{}".format(
            str(id), " " * (id_len - len(str(id))),
            client.host, " " * (host_len - len(client.host)),
            str(client.port), " " * (port_len - len(str(client.port))),
            client.user
        ))


class FtpConfigOptions(CommandOptions):
    COMMAND_ID = "ftpconfig" 
    SUBCOMMANDS = ["edit","add","show","list","remove","autobackup"]

    def __init__(self,app,cmd):
        CommandOptions.__init__(self,app,self.COMMAND_ID,cmd)
        self.__subcommand = "list"
        self.__interactive = True   # TODO get it from config
        self.__ftp_id = -1
        self.__host = None
        self.__port = None
        self.__user = None
        self.__password = None
        self.__backup_dir = None
        self.__use_tls = None
        self.__auto_backup = None
        self.__timeout = None
        self.__test = False
        self.__ftp_client = None

    @property
    def interactive(self):
        return self.__interactive
    @interactive.setter
    def interactive(self,b:bool):
        self.__interactive = b

    @property
    def subcommand(self):
        return self.__subcommand
    @subcommand.setter
    def subcommand(self,sc:str):
        if sc not in self.SUBCOMMANDS:
            raise ValueError("Unknown subcommand \"{subcommand}\"!".format(subcommand=sc))
            
        self.__subcommand = sc

    @property
    def ftp_id(self):
        return self.__ftp_id
    
    @ftp_id.setter
    def ftp_id(self,id:int):
        if self.subcommand == "create" and id != -1:
            try: 
                self.application.plugins.get('ftp').ftp.get(id)
                raise ValueError("FTP client with id \"{id}\" exists!".format(id))
            except LookupError:
                self.__ftp_id = id
        elif self.subcommand in ('show','remove','atuobackup'):
            try:
                self.__ftp_client = self.application.plugins.get('ftp').ftp.get(id)
            except LookupError:
                raise ValueError("FTP client with ID \"{id}\" does not exist".format(id=id))
        elif self.subcommand == 'edit':
            try:
                self.__ftp_client = self.application.plugins.get('ftp').ftp.get(id)
                if self.__host is None:
                    self.host = self.__ftp_client.host
                if self.__port is None:
                    self.port = self.__ftp_client.port
                if self.__user is None:
                    self.user = self.__ftp_client.user
                if self.__use_tls is None:
                    self.use_tls = self.__ftp_client.use_tls
                if self.__backup_dir is None:
                    self.backup_dir = self.__ftp_client.backup_dir
                if self.__auto_backup is None:
                    self.auto_backup = self.__ftp_client.auto_backup
                if self.__timeout is None:
                    self.timeout = self.__ftp_client.timeout
            except:
                raise ValueError("FTP client with ID \"{id}\" does not exist".format(id=id))
        self.__ftp_id = id
        
    @property
    def host(self):
        return self.__host
    @host.setter
    def host(self,host:str):
        self.__host = host
    
    @property
    def port(self):
        return self.__port
    @port.setter
    def port(self,port:int):
        if port > 65535:
            raise ValueError("Illegal port number!")
        self.__port = port
    
    @property
    def user(self):
        return self.__user
    @user.setter
    def user(self,user:str):
        self.__user = user

    @property
    def password(self):
        return self.__password
    @password.setter
    def password(self,passwd:str):
        self.__password=passwd

    @property
    def backup_dir(self):
        return self.__backup_dir
    @backup_dir.setter
    def backup_dir(self,bd:str):
        self.__backup_dir = bd

    @property
    def use_tls(self):
        return self.__use_tls
    @use_tls.setter
    def use_tls(self,tls:bool):
        self.__use_tls = tls

    @property
    def auto_backup(self):
        return self.__auto_backup
    @auto_backup.setter
    def auto_backup(self,enable:bool):
        self.__auto_backup = enable

    @property
    def test(self):
        return self.__test
    @test.setter
    def test(self,b:bool):
        self.__test = b

    @property
    def timeout(self):
        return self.__timeout
    @timeout.setter
    def timeout(self,timeout:int):
        self.__timeout = int(timeout)

    def get_ftp_client(self):
        if not self.__ftp_client:
            kwargs={'id':self.ftp_id}
            if self.__host is not None:
                kwargs['host'] = self.host
            if self.__port is not None:
                kwargs['port'] = self.port
            if self.__user is not None:
                kwargs['user'] = self.user
            if self.__password is not None:
                kwargs['password'] = self.password
            if self.__backup_dir is not None:
                kwargs['backup_dir'] = self.backup_dir
            if self.__use_tls is not None:
                kwargs['use_tls'] = self.use_tls
            if self.__auto_backup is not None:
                kwargs['auto_backup'] = self.auto_backup
            if self.__timeout is not None:
                kwargs['timeout'] = self.timeout

            self.__ftp_client = FtpClient(self.application,**kwargs)
        else:
            if self.__host is not None:
                self.__ftp_client.host = self.host
            if self.__port is not None:
                self.__ftp_client.port = self.port
            if self.__user is not None:
                self.__ftp_client.user = self.user
            if self.__password is not None:
                self.__ftp_client.password = self.password
            if self.__backup_dir is not None:
                if self.backup_dir == '.':
                    self.__ftp_client.backup_dir = ""
                else:
                    self.__ftp_client.backup_dir = self.backup_dir
            if self.__use_tls is not None:
                self.__ftp_client.use_tls = self.use_tls
            if self.__auto_backup is not None:
                self.__ftp_client.auto_backup = self.auto_backup
            if self.__timeout is not None:
                self.__ftp_client.timeout = self.timeout

        return self.__ftp_client

class FtpConfig(Command):
    def __init__(self,app):
        Command.__init__(self,app,FtpConfigOptions.COMMAND_ID,"Create/Edit FTP settings")

    def get_synopsis(self, command=None):
        if command is None:
            command = self.id
        return """{command} [list]
{command} [show|remove] FTPID
{command} autobackup <enable|disable> [FTPID]
{command} edit [-i|--interactive|-I|--no-iteractive] [-h|--host HOST] 
    [-p|--port PORT] [-U|--user USER] [-P|--password PASSWORD]
    [-T|--tls USE_TLS] [-b|--backupdir BACKUPDIR] [--test] 
    [-t|--timeout TIMEOUT] FTPID
{command} add [-i|--interactive|-I|--no-interactive] [-h|--host HOST]
    [-p|--port PORT] [-U|--user USER] [-P|--password PASSWORD]
    [-T|--tls USE_TLS] [-b|--backupdir BACKUPDIR] [--test] 
    [-t|--timeout TIMOUT] [FTPID]""".format(command=command)

    def ftp_settings_interactive(self,options:FtpConfigOptions):
        settings_ok = False
        while not settings_ok:
            if options.subcommand == 'add':
                value_ok = False
                while not value_ok:
                    try:
                        value = input("FTPID [{}]: ".format(options.ftp_id))
                        if value:
                            options.ftp_id = int(value)
                        value_ok = True
                    except Exception as err:
                        print(err)

            value_ok = False
            while not value_ok:
                if options.host is None:
                    host = "localhost"
                else:
                    host = options.host
                value = input("Host [{}]: ".format(host))
                if value:
                    options.host = value
                if options.host:
                    value_ok = True

            value_ok = False
            while not value_ok:
                if options.port is None:
                    port = 21
                else:
                    port = options.port
                value = input("Port [{}]: ".format(str(port)))
                try:
                    if value:
                        options.port = int(value)
                    value_ok = True
                except Exception as err:
                    print(err)

            value_ok = False
            while not value_ok:
                if options.user is None:
                    user = "anonymous"
                else:
                    user = options.user
                value = input("User [{}]: ".format(user))
                if value:
                    options.user = value
                if options.user:
                    value_ok = True

            value = getpass.getpass("Password: ")
            if value:
                options.password = value

            if options.backup_dir is None:
                backupdir = ""
            else:
                backupdir = options.backup_dir
            value = input("FTP BackupDir [{}]: ".format(backupdir))
            if value:
                options.backup_dir = value

            value = input("Use TLS [Y/N]? ")
            if value.lower() in ("y","yes","1","on","true"):
                options.use_tls = True
            else:
                options.use_tls = False

            value = input("Enable autobackup [Y/N]? ")
            if value.lower() in ("y","yes","1","on","true"):
                options.auto_backup = True
            else:
                options.auto_backup = False

            if options.use_tls:
                tls = "YES"
            else:
                tls = "NO"
            
            if options.auto_backup:
                autobackup = "YES"
            else:
                autobackup = "NO"

            title="FTP SETTINGS"
            print("*" * 80 + "\n* " + title + " " * (77 - len(title)) + "*\n" + "*" * 80)
            print("FTPID:            {}".format(options.ftp_id))
            print("Host:             {}".format(options.host))
            print("Port:             {}".format(options.port))
            print("User:             {}".format(options.user))
            print("Password:         {}".format("*" * 8))
            print("Timeout:          {}".format(options.timeout))
            print("Backup Directory: {}".format(options.backup_dir))
            print("Use TLS           {}".format(tls))
            print("Enable automatic Backups: {}".format(autobackup))
            if options.test:
                value = "y"
            else:
                value = input("Test settings [Y/N]? ")
            if value.lower() == "y":
                ftp = options.get_ftp_client()
                if ftp.ftp_connect():
                    ftp.close()
                    settings_ok = True                
            else:
                value = input("OK [Y/N]? ")
                if value.lower() == "y":
                    settings_ok = True

        return options
           

    def do_parse(self, cmd, argv):
        options = FtpConfigOptions(self.application,cmd)
        if len(argv) == 0 or argv[0] == 'list':
            return options
        elif argv[0] in ['show','remove']:
            options.subcommand = argv[0]
            if len(argv) < 2:
                raise OptionError("Missing argument FTPID!")
            options.ftp_id = int(argv[1])
        elif argv[0] in ['add','edit']:
            try:
                options.subcommand=argv[0]
            except ValueError as err:
                raise OptionError(err.args[0])
            
            try:
                opts,args = getopt.getopt(argv[1:],
                                          "AaiIh:p:U:p:t:b:T",
                                          [
                                            "autobackup"
                                            "no-autobackup"
                                            "interactive",
                                            "no-interactive",
                                            "host=",
                                            "port=",
                                            "user=",
                                            "password=",
                                            "backupdir=",
                                            "tls=",
                                            "timeout=",
                                            "test",
                                            "no-test"
                                          ])
            except getopt.GetoptError as err:
                raise OptionError("Illegal commandline! ({message})".format(message=err))
            
            for o,a in opts:
                if o in ("-i","--interactive"):
                    options.interactive = True
                elif o in ("-I","--no-interactive"):
                    options.interactive = False
                elif o in ("-h","--host"):
                    options.host = a
                elif o in ('-p','--port'):
                    try:
                        options.port = int(a)
                    except Exception as err:
                        raise OptionError("port needs to be a number less than 65536! ({message})".format(message=err))
                elif o in ('-U','--user'):
                    options.user = a
                elif o in ('-P','--password'):
                    options.password = a
                elif o in ('-b','--backupdir'):
                    options.backup_dir = a
                elif o in ('-T','--tls'):
                    if a.lower() in ('y','yes','true','on','1'):
                        options.use_tls = True
                    else:
                        options.use_tls = False
                elif o in ('-T','--timeout'):
                    options.timeout = int(a)
                elif o in ('-a','--autobackup'):
                    options.auto_backup = True
                elif o in ('-A','--no-autobackup'):
                    options.auto_backup = False
                elif o == '--test':
                    options.test = True
                elif o == '--no-test':
                    options.test = False

            if len(args) > 0:
                try:
                    ftpid = int(args[0])
                except Exception as err:
                    raise OptionError("FTPID needs to be an integer! ({message})".format(message=err))
                try:
                    options.ftp_id = ftpid
                except Exception as err:
                    raise OptionError(str(err))
                    

            if options.subcommand == "edit" and options.ftp_id == -1:
                raise OptionError("Missing argument FTPID!")
        elif argv[0] == "autobackup":
            options.subcommand = argv[0]
            if len(argv) == 1:
                raise OptionError("Missing argument \"enable\" or \"disable\" for subcommand {subcommand}!".format(subcommand=argv[0]))
            if argv[1] == "enable":
                options.auto_backup = True
            elif argv[1] == "disable":
                options.auto_backup = False
            else:
                raise OptionError("Argument \"enable\" or \"disable\" required!")
            
            if len(argv) > 2:
                try:
                    options.ftp_id = int(argv[2])
                except Exception as err:
                    raise OptionError("Illegal FTPID! ({message})".format(message=str(err)))
        else:
            raise OptionError("Unknown subcommand \"{subcommand}\"!".format(subcommand=argv[0]))
        
        return options
            
    def do_execute(self, options:FtpConfigOptions):
        if options.subcommand == "list":
            _print_ftp_list(self.application.plugins.get('ftp'))
            return 0
        elif options.subcommand == "show":
            plugin = self.application.plugins.get('ftp')
            try:
                ftp = plugin.ftp.get(options.ftp_id)
            except Exception as err:
                print(err)
                return 1
            
            print("FTPID: {}".format(ftp.id))
            print("Host: {}".format(ftp.host))
            print("Port: {}".format(str(ftp.port)))
            print("User: {}".format(ftp.user))
            print("Password: {}".format("*" * 8))
            print("Timeout: {}".format(ftp.timeout))
            print("Backup Directory: {}".format(ftp.backup_dir))
            if ftp.use_tls:
                use_tls = "YES"
            else:
                use_tls = "NO"
            print("Use TLS: {}".format(use_tls))

            if ftp.auto_backup:
                autobackup = "YES"
            else:
                autobackup = "NO"
            print("Autobackup {}".format(autobackup))

            return 0
        elif options.subcommand == "add":
            if options.interactive:
                options = self.ftp_settings_interactive(options)
            ftpclient = options.get_ftp_client()
            if options.test:
                if not ftpclient.ftp_connect():
                    print("Unable to connect to host!",file=sys.stderr)
                    return 3
                ftpclient.close()
            ftpclient.save()
            plugin = self.application.plugins.get('ftp').ftp.add(ftpclient)
            return 0
        elif options.subcommand == "edit":
            if options.interactive:
                options = self.ftp_settings_interactive(options)
            ftpclient = options.get_ftp_client()
            if options.test:
                if not ftpclient.ftp_connect():
                    print("Unable to connect to host!",file=sys.stderr)
                    return 3
                ftpclient.close()
            ftpclient.save()
            return 0
        elif options.subcommand == 'remove':
            self.application.plugins.get('ftp').ftp.remove(options.ftp_id)
            try:
                self.application.config.keyfile.remove_group('plugin:ftp:{}'.format(options.ftp_id))
            except:
                pass
            return 0
        elif options.subcommand == "autobackup":
            if options.ftp_id > 0:
                options.get_ftp_client().save()
            else:
                for ftpclient in self.application.plugins.get('ftp').ftp.clients.values():
                    ftpclient.auto_backup = options.auto_backup
                    ftpclient.save()
        return 10
     
class FtpOptions(CommandOptions):
    COMMAND_ID = "ftp"
    SUBCOMMANDS = ['list','synchronize','fetch-all']
    def __init__(self,app,cmd):
        CommandOptions.__init__(self,app,self.COMMAND_ID,cmd)
        self.__subcommand = 'list'
        self.__ftp_id = None
        self.__ftp_client = None

    @property
    def subcommand(self):
        return self.__subcommand
    @subcommand.setter
    def subcommand(self,sc:str):
        if not sc in self.SUBCOMMANDS:
            raise ValueError("Unknown subcommand \"{subcommand}\"!".format(subcommand=sc))
        self.__subcommand = sc

    @property
    def ftp_id(self):
        return self.__ftp_id
    @ftp_id.setter
    def ftp_id(self,id:int):
        try:
            self.__ftp_client = self.application.plugins.get('ftp').ftp.get(int(id))
            self.__ftp_id = id
        except LookupError:
            raise ValueError("No FTP client with ID \"{id}\" exists!".format(id=id))
        except:
            raise TypeError("Illegal type for ftpid")
        
    @property
    def ftp_client(self):
        return self.__ftp_client
    
class Ftp(Command):
    def __init__(self,app):
        Command.__init__(self,app,FtpOptions.COMMAND_ID,'FTP actions')

    def get_synopsis(self,command=None):
        if command is None:
            command = FtpOptions.COMMAND_ID

        return """{command} [list]
{command} synchronize [FTPID]"""

    def do_parse(self, cmd, argv):
        options = FtpOptions(self.application,cmd)
        if len(argv) == 0 or argv[0] == 'list':
            return options
        elif argv[0] == 'synchronize':
            options.subcommand = argv[0]
            if len(argv) > 1:
                options.ftp_id = argv[1]
        elif argv[0] == 'fetch-all':
            options.subcommand = argv[0]
            if len(argv) > 1:
                options.ftp_id == argv[1]
            else:
                for i in self.application.plugins.get('ftp').ftp.clients.keys():
                    options.ftp_id = i
                    break

        else:
            try:
                options.subcommand = argv[0]
            except Exception as err:
                raise OptionError(str(err))
            
        return options
        
    def do_execute(self, options:FtpOptions):
        if options.subcommand == 'list':
           _print_ftp_list(self.application.plugins.get('ftp'))
           return 0
        elif options.subcommand == 'synchronize':
            if options.ftp_client is not None:
                options.ftp_client.synchronize()
            else:
                for ftp_client in self.application.plugins.get('ftp').ftp.clients.values():
                    ftp_client.synchronize()
            return 0
        elif options.subcommand == 'fetch-all':
            options.ftp_client.fetch_all()
        return 1
    
COMMANDS = [
    (FtpConfig,("ftp-config",)),
    (Ftp,None),
]
