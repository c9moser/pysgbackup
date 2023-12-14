# -*- coding: utf-8 -*-

from ..command import CommandOptions, Command, CommandOptions_None
from .. import steam
from ..error import OptionError
from .game import GameOptions
from ..game import Game
import os
import sys

from ..help import get_builtin_help
class SteamlibOptions(CommandOptions):
    (MODE_LIST,MODE_ADD,MODE_REMOVE) = range(3)

    def __init__(self,app,cmd):
        CommandOptions.__init__(self,app,'steamlib',cmd)
        self.__mode = self.MODE_LIST
        self.__path = None

    @property
    def mode(self):
        return self.__mode
    @mode.setter
    def mode(self,mode:int):
        if (mode < self.MODE_LIST or mode > self.MODE_REMOVE):
            raise ValueError("Illegal value for mode")
        self.__mode = mode
        
    @property
    def path(self):
        return self.__path
    @path.setter
    def path(self,p:str):
        if not os.path.isabs(p):
            raise ValueError('"path" needs to be an absolute path!')
        self.__path = p

    @property
    def steamlib(self):
        if (self.mode == self.MODE_ADD) and self.path:
            return steam.SteamLib(self.application,self.path)
        return None
    
    @property
    def is_valid(self):
        if (self.mode == self.MODE_LIST):
            return True
        elif (self.mode == self.MODE_ADD):
            lib = self.steamlib
            return (isinstance(lib,steam.SteamLib) and lib.is_valid)
        elif (self.mode == self.MODE_REMOVE and self.path and os.path.isabs(self.path)):
            return True
        return False
    
class Steamlib(Command):
    def __init__(self,app):
        Command.__init__(self,app,'steamlib',"Steam Library commands.")

    def get_synopsis(self,command=None):
        if command is None:
            command = self.id
        return "sgbackup {command} [list|add <PATH>|remove <PATH>]".format(command=command)

    def get_help(self,command=None):
        if command is None:
            command = self.id
        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)
    
    def parse_vfunc(self, cmd, argv):
        options = SteamlibOptions(self.application,cmd)

        if len(argv) > 0:
            if (argv[0] == 'list'):
                options.mode = SteamlibOptions.MODE_LIST
                pass
            elif (argv[0] == 'add'):
                if len(argv) < 2:
                    raise OptionError("No SteamLib-path to add specified!")
                try:
                    options.path = argv[1]
                    options.mode = SteamlibOptions.MODE_ADD
                except Exception as err:
                    raise OptionError("Invalid path to add given! ({message})".format(message=err.args[0]))
            elif (argv[0] == 'remove'):
                if len(argv) < 2:
                    raise OptionError("No SteamLib-path to remove specified!")
                try:
                    options.path = argv[1]
                    options.mode = SteamlibOptions.MODE_REMOVE
                except Exception as err:
                    raise OptionError("Invalid path to remove given! ({message})".format(message=err.args[0]))
                
        if (not options.is_valid):
            raise OptionError("Invalid arguments for \"{command}\" command!".format(command=cmd))

        return options
    
    def execute_vfunc(self, options:SteamlibOptions):
        if (options.mode == SteamlibOptions.MODE_LIST):
            for sl in self.application.steam.libraries:
                print(sl.path)
        elif (options.mode == SteamlibOptions.MODE_ADD):
            sl = options.steamlib
            if isinstance(sl,steam.SteamLib) and sl.is_valid:
                self.application.steam.add_library(sl)
            self.application.config.save()
        elif (options.mode == SteamlibOptions.MODE_REMOVE):
            self.application.steam.remove_library(options.path)
            self.application.config.save()
    # execute_vfunc()
# Steamlib class

class SteamOptions(CommandOptions):
    COMMANDS = ['list','scan','update','new','ignored']

    def __init__(self,app,cmd):
        CommandOptions.__init__(self,app,'steam',cmd)
        self.__command = 'list'

    @property
    def command(self):
        return self.__command
    @command.setter
    def command(self,c:str):
        if c not in self.COMMANDS:
            raise ValueError("\"{command}\" is not a valid steam command!".format(command=c))
        self.__command = c

class Steam(Command):   
    def __init__(self,app):
        Command.__init__(self,app,"steam","Manage steam Apps.")

    def get_synopsis(self,command=None):
        if command is None:
            command = self.id
        return "sgbackup {command} [ignored|list|new|scan|update]".format(command=command)

    def get_help(self,command=None):
        if command is None:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)
    
    def config_steamapp(self,appid,acf,steamlib):
        done=False
        print("=" * 80)
        print("= " + "CONFIGURE: " + acf['name'])
        print("=" * 80)
        
        while not done:
            x = input("Do you want to [A]dd, [I]gnore or [S]kip this steamapp? ")
            if x.lower() in ("s","skip"):
                return
            elif x.lower() in ("i","ignore"):
                self.application.steam.appid_ignore.add(appid)
                self.application.steam.appid_ignore.save()
                return
            elif x.lower() in ("a"):
                done=True
        
        done=False
        game_id=""
        game_name=acf['name']
        installdir=os.path.join(steamlib.path,"steamapps","common",acf["installdir"])
        if sys.platform == 'win32':
            installdir=installdir.replace("/","\\")

        game = None
        while not done:
            ok=False
            if game is not None:
                game_id = game.game_id

            while not ok:
                if game_id:
                    x = input("GameID [{game_id}]: ".format(game_id=game_id))
                else:
                    x = input("GameID: ")
                if x:
                    game_id = x
                if game_id:
                    ok = True

            if game is None:
                game = Game(self.application,game_id,game_name,game_id,installdir=installdir,steam_appid=appid)
            else:
                game.game_id = game_id

            x = input("Game Name [{game_name}]: ".format(game_name=game.game_name))
            if x:
                game.game_name = x

            if not game.savegame_name:
                game.savegname_name = game_id
            x = input("SaveGame name [{sgname}]: ".format(sgname=game.savegame_name))
            if x:
                game.savegame_name = x

            ok = False
            while not ok:
                if game.savegame_root:
                    x = input("SaveGame root [{sgroot}]: ".format(sgroot=game.savegame_root_template))
                else:
                    x = input("SaveGame root: ")

                if x:
                    if sys.platform == 'win32':
                        game.savegame_root = x.replace("/","\\")
                    else:
                        game.savegame_root = x

                if game.savegame_root:
                    ok = True

            ok = False
            while not ok:
                if game.savegame_dir:
                    x = input("SaveGame dir [{sgdir}]: ".format(sgdir=game.savegame_dir_template))
                else:
                    x = input("SaveGame dir: ")

                if x:
                    if sys.platform == 'win32':
                        game.savegame_dir = x.replace("/","\\")
                    else:
                        game.savegame_dir = x

                if game.savegame_dir:
                    ok = True


            print("Installdir: {installdir}".format(installdir=game.installdir))
            print("Steam AppID: {appid}".format(appid=game.steam_appid))

            print('-' * 80)
            print("CONFGURATION:\n")
            print("GameID: {game_id}".format(game_id=game.game_id))
            print("Game name: {game_name}".format(game_name=game.game_name))
            print("SaveGame name: {sgname}".format(sgname=game.savegame_name))
            print("SaveGame root raw: {sgroot}".format(sgroot=game.savegame_root_template))
            print("SaveGame root: {sgroot}".format(sgroot=game.savegame_root))
            print("SaveGame dir raw: {sgdir}".format(sgdir=game.savegame_dir_template))
            print("SaveGame dir: {sgdir}".format(sgdir=game.savegame_dir))
            print("Installdir: {installdir}".format(installdir=game.installdir))
            print("Steam AppID: {appid}".format(appid=game.steam_appid))
            print("")
            x = input("Does this look reasonable? [Y]es [N]o: ")
            if (x.lower() in ("y","yes")):
                done = True

        # while not done
        game.save()
    
    def parse_vfunc(self, cmd, argv):
        if len(argv) < 1:
            steam_cmd = 'list'
        else:
            steam_cmd = argv[0]

        options = SteamOptions(self.application,cmd)
        if steam_cmd in options.COMMANDS:
            options.command = steam_cmd
        else:
            raise OptionError("Unknown \"sgbackup steam\" command \"{command}\"!".format(command=steam_cmd))
        
        return options

    def execute_vfunc(self, options):
        if options.command == 'list':
            appid_len = 0
            gameid_len = 0
            for appid,game in self.application.games.steam_items:
                x = len((str(appid)))
                if x > appid_len:
                    appid_len = x

                x = len(game.game_id)
                if x > gameid_len:
                    gameid_len = x

            appid_len = ((appid_len // 4) + 1) * 4
            gameid_len = ((gameid_len // 4) + 1) * 4

            for appid,game in self.application.games.steam_items:
                sappid = str(appid)
                s0 = " " * (appid_len - len(sappid))
                s1 = " " * (gameid_len - len(game.game_id))
                print("{appid}{s0}{gid}{s1}\"{name}\"".format(appid=appid,s0=s0,gid=game.game_id,s1=s1,name=game.game_name))

        elif options.command == 'new':
            appid_len = 0
            unregistered_apps = self.application.steam.unregistered_apps
            for appid in unregistered_apps.keys():
                if len(str(appid)) > appid_len:
                    appid_len = len(str(appid))

            appid_len = (((appid_len // 4) + 1) * 4)

            for appid,spec in unregistered_apps.items():
                print("{}{}{}".format(str(appid)," " * (appid_len - len(str(appid))),spec['acf']['name']))

        elif options.command == 'scan':
            apps =  self.application.steam.unregistered_apps
            appids = sorted(apps.keys())

            for appid in appids:
                self.config_steamapp(appid,apps[appid]['acf'],apps[appid]['library'])
                
        elif options.command == 'update':
            self.application.steam.update_games(False)

        elif options.command == 'ignored':
            steamapps = dict([(k,v) for k,v in self.application.steam.apps.items() 
                              if k in self.application.steam.ignore_appids])
            appid_len = 0
            for i in steamapps.keys():
                if len(str(i)) > appid_len:
                    appid_len = len(str(i))

            appid_len = (((appid_len // 4) + 1) * 4)

            keys = sorted(steamapps.keys())
            for k in keys:
                print("{}{}{}".format(k," " * (appid_len - len(str(k))),steamapps[k]['acf']['name']))          

        return 0
    
COMMANDS = [
    (Steamlib,None),
    (Steam,None),
]