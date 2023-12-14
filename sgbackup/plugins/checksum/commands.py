from sgbackup.command import Command,CommandOptions
from .settings import PLUGIN_ID,CHECKSUMS
from .checksum import create_missing_checksums,check_all_checksums,check_checksums_for_game
from sgbackup.game import Game
from sgbackup.error import OptionError
import getopt
import os
class ChecksumOptions(CommandOptions):
    COMMAND_ID = "checksum"
    SUBCOMMANDS = ['list','create-missing','check']

    def __init__(self,app,cmd):
        CommandOptions.__init__(self,app,self.COMMAND_ID,cmd)
        self.__subcommand = 'list'
        self.__game = None
        self.__check_delete_failed = False

    @property
    def subcommand(self):
        return self.__subcommand
    @subcommand.setter
    def subcommand(self,sc):
        if sc not in self.SUBCOMMANDS:
            raise ValueError("Illegal subcommand {subcommand}!".format(subcommand=sc))
        self.__subcommand = sc

    @property
    def check_delete_failed(self):
        return self.__check_delete_failed
    @check_delete_failed.setter
    def check_delete_failed(self,b:bool):
        self.__check_delete_failed = b

    @property
    def game(self):
        return self.__game
    @game.setter
    def game(self,game):
        if isinstance(game,Game):
            self.__game = game
        else:
            self.__game = self.application.games.get(game)

        

class Checksum(Command):
    def __init__(self,app):
        Command.__init__(self,app,ChecksumOptions.COMMAND_ID,"Checksum operations")

    def get_synopsis(self,command=None):
        if command is None:
            command = self.id
        return """{command} [list|create-missing]
{command} check [-d|--delete] [GAME]""".format(command=command)

    def parse_vfunc(self, cmd, argv):
        options = ChecksumOptions(self.application,cmd)

        if len(argv) == 0 or argv[0] == 'list':
            pass
        elif argv[0] == 'create-missing':
            options.subcommand = argv[0]
        elif argv[0] == 'check':
            options.subcommand = argv[0]
            
            if len(argv) > 1:
                try:
                    opts,args = getopt.getopt(argv[1],'d',['delete'])
                except getopt.GetoptError as err:
                    raise OptionError(str(err))

                for o,a in opts:
                    if o in ("-d","--delete"):
                        options.check_delete_failed = True

                if args:
                    try:
                        if isinstance(args,str):
                            options.game = args
                        else:
                            options.game = args[0]
                    except Exception as err:
                        raise OptionError("Illegal argument for GAME! ({message})".format(message=err))
                    
        return options

    def execute_vfunc(self, options:ChecksumOptions):

        if options.subcommand == 'list':
            for i in CHECKSUMS:
                print(i)
            return 0
        elif options.subcommand == 'create-missing':
            create_missing_checksums(self.application)
            return 0
        elif options.subcommand == "check":
            if options.check_delete_failed:
                failed_cb = lambda a,g,f: a.archivers.delete_backup(g,f)
            else:
                failed_cb = None

            if options.game is not None:
                check_checksums_for_game(self.application,options.game,failed_callback=failed_cb)
            else:
                check_all_checksums(self.application,failed_callback=failed_cb)
            return 0
        return 1

COMMANDS=[(Checksum,None)]