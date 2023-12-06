# -*- coding: utf-8 -*-

# Author: Christian Moser
# License: GPL
# File: sgbackup/commands/game.py
# Module: sgbackup.commands.game

from sgbackup.command import CommandOptions
from ..command import Command,CommandOptions
from ..game import Game
import getopt
from .. import error
from ..help import get_builtin_help
import os,sys

class GameOptions(CommandOptions):
    OPTION_ID = "command-game-options"

    def __init__(self,app,command,game=None,interactive=True):
        CommandOptions.__init__(self,app,self.OPTION_ID,command)
        if not game:
            self.__game_id=""
            self.__game_name=""
            self.__savegame_name=""
            self.__savegame_root=""
            self.__savegame_dir=""
            self.__installdir=""
            self.__steam_appid=0
            self.__variables={}
            self.__game = None
            self.__interactive = interactive
        else:
            self.__game_id=game.game_id
            self.__game_name=game.game_name
            self.__savegame_name=game.savegame_name
            self.__savegame_root=game.savegame_root
            self.__savegame_dir=game.savegame_dir
            self.__installdir=game.installdir
            self.__steam_appid=game.steam_appid
            self.__variables=game.raw_variables
            self.__game=game
            self.__interactive = interactive

    @property
    def game_id(self):
        return self.__game_id
    @game_id.setter
    def game_id(self,gid:str):
        self.__game_id = gid

    @property
    def game_name(self):
        return self.__game_name
    @game_name.setter
    def game_name(self,name:str):
        self.__game_name = name

    @property
    def savegame_name(self):
        return self.__savegame_name
    @savegame_name.setter
    def savegame_name(self,name:str):
        self.__savegame_name = name

    @property
    def savegame_root(self):
        return self.__savegame_root
    @savegame_root.setter
    def savegame_root(self,sgroot:str):
        self.__savegame_root = sgroot

    @property
    def savegame_dir(self):
        return self.__savegame_dir
    @savegame_dir.setter
    def savegame_dir(self,sgdir:str):
        self.__savegame_dir = sgdir

    @property
    def installdir(self):
        return self.__installdir
    @installdir.setter
    def installdir(self,idir:str):
        self.__installdir = idir

    @property
    def steam_appid(self):
        return self.__steam_appid
    @steam_appid.setter
    def steam_appid(self,appid:int):
        self.__steam_appid = appid

    @property
    def interactive(self):
        return self.__interactive
    @interactive.setter
    def interactive(self,b:bool):
        self.__interactive = b

    @property
    def variables(self):
        return self.__variables
    
    @property
    def game(self):
        return self.__game
    @game.setter
    def game(self,game:Game):
        self.__game = game
    
    def create_game(self):
        return Game(
            self.game_id,
            self.game_name,
            self.savegame_name,
            self.savegame_root,
            self.savegame_dir,
            self.steam_appid,
            self.installdir,
            False,
            self.variables)
    
    def update_game(self):
        if not self.game:
            return self.create_game()
        
        self.game.name = self.game_name
        self.game.savegame_name = self.savegame_name
        self.game.savegame_root = self.savegame_root
        self.game.savegame_dir = self.savegame_dir
        self.game.steam_appid = self.steam_appid
        self.game.installdir = self.installdir
        
        delvars=[]
        for var in self.game.raw_variables.keys():
            if var not in self.variables:
                delvars.append(var)

        for var in delvars:
            self.game.remove_variable(var)

        for vname,vvalue in self.variables.items():
            self.game.set_variable(vname,vvalue)

        self.game.game_id = self.game_id

        return self.game            

    @property
    def is_valid(self):
        return (self.game_id and self.game_name and self.savegame_name and self.savegame_dir and self.savegame_root)
    
    def add_variable(self,name:str,value=""):
        self.__variables[name] = value

    def remove_variable(self,name:str):
        if name in self.__variables:
            del self.__variables[name]

    def get_variable(self,name:str):
        if not name in self.__variables:
            raise LookupError("Variable \"{}\" not found!".format(name))
        return self.__variables[name]
# GameOptions class
    
class AddGame(Command):
    def __init__(self,app):
        Command.__init__(self,app,"add-game","Add a game to back up.")

    def get_synopsis(self,command=None):
        if command is None:
            command = self.id
        return """sgbackup {command} [-iI|--interactive|--no-interactive]
    [-n|--name <NAME>] [-r|--root <SGROOT>] [-d|--dir <SGDIR>]
    [-N|--savegame-name <SGNAME>] [-s|--steam <APPID>] 
    [-x|--installdir <DIR>] [-V|--variable NAME=VALUE ...] <GAME_ID>""".format(command=command)
    
    def get_help(self,command=None):
        if command is None:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)
    
    def do_parse(self, cmd, argv):
        try: 
            opts,args = getopt.getopt(
                argv,
                'd:IiN:n:r:s:V:x:',
                [
                    'interactive',
                    'no-interactive',
                    'name=',
                    'root=',
                    'dir=',
                    'savegame-name=',
                    'steam=',
                    'installdir=',
                    'variable='
                ])
            
        except getopt.GetoptError as err:
            raise error.OptionError(err.args[0])
        
        options = GameOptions(self.application,cmd,
                              interactive=self.application.config.get_boolean('commandGame','addGameInteractive',True))

        for o,v in opts:
            if (o == '-i' or o == '--interactive'):
                options.interactive = True
            elif (o == '-I' or o == '--no-interactive'):
                options.interactive = False
            elif (o == '-n' or o == '--name'):
                options.game_name = v
            elif (o == '-N' or o == '--savegame-name'):
                options.savegame_name = v
            elif (o == '-r' or o == '--root'):
                options.savegame_root = v
            elif (o == '-d' or o == '--dir'):
                options.savegame_dir = v
            elif (o == '-s' or o == '--steam'):
                try:
                    options.steam_appid = int(v)
                except:
                    pass
            elif (o == '-x' or o == 'intalldir'):
                options.installdir = v
            elif (o == '-V' or o == '--variable'):
                if ('=' in v):
                    name,value = v.split('=',1)
                    options.add_variable(name,value)
                else:
                    options.add_variable(name,"")
        
        if (len(args) > 1):
            raise error.OptionError("Too many arguments!")
        elif (len(args) < 1):
            raise error.OptionError("No GameID given!")
        
        options.game_id = args[0]
        return options
    
    def config_game_interactive(self,options:GameOptions):
        def get_edit_variables():
            edit = ""
            while edit.lower() not in ('a','e','s','n'):
                edit = input("Edit Variables? [A]dd/[D]elete/[E]dit/[S]hoe/[N]o: ")

            return edit
        # get_edit_variables()

        edit_done = False
        while not edit_done:
            print(("=" * 80) + "\n= Add new Game\n" + ("=" * 80))
            gid = input("Game ID [{}]: ".format(options.game_id))
            if (len(gid) > 0):
                options.game_id = gid
            
            name = input("Game name [{}]: ".format(options.game_name))
            if (len(name) > 0):
                options.game_name = name

            if options.savegame_name:
                sgname_default = options.savegame_name
            else:
                sgname_default = options.game_id

            sgname = input("Savegame Name [{}]: ".format(sgname_default))
            if len(sgname) > 1:
                options.savegame_name = sgname
            else:
                options.savegame_name = sgname_default

            sgroot = input("Savegame root-dir [{}]: ".format(options.savegame_root))
            if len(sgroot) > 0:
                options.savegame_root = sgroot

            sgdir = input("Savegame directory [{}]: ".format(options.savegame_dir))
            if len(sgdir) > 0:
                options.savegame_dir = sgdir

            installdir = input("Game installdir [{}]: ".format(options.installdir))
            if (len(installdir)) > 0:
                if (installdir == ":delete:"):
                    options.installdir = ""
                else:
                    options.installdir = installdir

            steam_appid_is_valid = False
            while not steam_appid_is_valid:
                steam_appid = input("Steam AppID [{}]: ".format(options.steam_appid))
                if not steam_appid:
                    steam_appid_is_valid = True
                else:
                    try:
                        options.steam_appid = abs(int(steam_appid))
                        steam_appid_is_valid = True
                    except:
                        steam_appid_is_valid = False

            edit_variables = get_edit_variables()
            while edit_variables.lower() != 'n':
                while edit_variables.lower() in ('a','e','s'):
                    if (edit_variables.lower() == 'a'):
                        vname = ""
                        while not vname:
                            vname = input("Variable: ")
                        vvalue = input("Value: ")
                        options.add_variable(vname,vvalue)
                        edit_variables = get_edit_variables()
                    elif (edit_variables.lower() == 'd'):
                        count = 0
                        vars = {}
                        for var,value in options.variables.items():
                            count += 1
                            vars[count] = (var,value)

                        for id,v in vars.items():
                            print("{}\t{}={}".format(id,v[0],v[1]))

                        var_ok = False
                        while not var_ok:
                            try:
                                variable = int(input("Select variable ([0] to abort): "))
                                if variable == 0:
                                    var_ok = True
                                    break
                                if variable in vars:
                                    options.remove_variable(vars[variable][0])
                                    var_ok = True
                            except:
                                pass
                        edit_variables = get_edit_variables()
                    elif (edit_variables.lower() == 'e'):
                        count = 0
                        vars = {}
                        for var,value in options.variables.items():
                            count += 1
                            vars[count] = (var,value)

                        for count,v in vars.items():
                            print ("{}\t{}={}".format(count,v[0],v[1]))

                        var_ok = False
                        while not var_ok:
                            try:
                                variable = int(input("Select Variable ([0] to abort): "))
                                if variable == 0:
                                    break
                                if variable in vars:
                                    var_name = vars[variable][0]
                                    var_value = vars[variable][1]

                                    vname = input("Variable [{}]: ".format(var_name))
                                    if not vname:
                                        vname = var_name
                                    
                                    vvalue = input("Value [{}]: ".format(var_value))
                                    if not vvalue:
                                        vvalue = var_value
                                    else:
                                        if vvalue == ':delete:':
                                            vvalue = ""

                                    if vname != var_name:
                                        options.remove_variable(var_name)
                                    options.variables[vname] = vvalue
                                    var_ok = True
                            except:
                                pass
                        edit_variables = get_edit_variables()
                    elif (edit_variables.lower() == 's'):
                        for var,value in options.variables:
                            print("{}={}".format(var,value))
                        edit_variables = get_edit_variables()

            if not options.is_valid():
                print("Settings are not valid! Restarting edit!")
                continue

            print(("-"*80) + "\n" + "Game Settings:")
            game_settings=[
                ("Game ID:",options.game_id),
                ("Game name:",options.game_name),
                ("Savegame name:",options.savegame_name),
                ("Savegame root:",options.savegame_root),
                ("Savegame dir:",options.savegame_dir),
                ("Game installdir:",options.installdir),
                ("Steam AppID:",str(options.steam_appid))
            ]

            name_len = 0
            for name,value in game_settings:
                if len(name) > name_len:
                    name_len = len(name)

            name_len += 1

            for name,value in game_settings:
                print (name + (" " * (name_len - len(name))) + value)
            print("VARIABLES:")
            for var,value in options.variables.values():
                print("  {}={}".format(var,value))

            print("\n")
            ok = ""
            while (ok.lower() not in ('y','n')):
                ok = input("Does this seem reasonable? [Y]es/[N]o: ")
            
            if ok.lower() == 'y':
                edit_done = True
                return True
        return False

    def do_execute(self, options):
        if not isinstance(options,GameOptions):
            raise TypeError("\"options\" is not a \"sgbackup.commands.game.GameOptions\" instance!")
        
        if options.interactive:
            self.config_game_interactive(options)

        if options.is_valid:
            game = options.create_game()
            game.save()
            self.application.games.add(game)
            print("Game {id}: \"{name}\" succesfully added!".format(id=game.game_id,name=game.game_name))
            return 0
        
        print("Adding game {id}: \"{name}\" failed!".format(id=game.game_id,name=game.game_name),file=sys.stderr)
        return 1
# AddGame class

class EditGame(Command):
    def __init__(self,app):
        Command.__init__(self,app,"edit-game","Edit game settings.")

    def get_synopsis(self,command=None):
        if command is None:
            command = self.id
        return """sgbackup edit-game [-i|-I|--interactive
    |--no-interactive] [-g|--id <NEW_GAME_ID>] 
    [-n|--name <NAME>] [-r|--root <SGROOT>] [-d|--dir <SGDIR>] 
    [-N|--savegame-name <SGNAME>] [-s|--steam <APPID>]
    [-x|--installdir <DIR>] [-V|--variable <NAME=VALUE> ...]
    [-R|--remove-variable <VARIABLE>] <GAME_ID>""".format(command=command)
    
    def get_help(self,command=None):
        if not command:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)
    
    def do_parse(self,cmd,argv):
        try:
            opts,args = getopt.getopt(argv,'d:g:iIn:N:r:R:s:V:x:',
                                      [
                                          'dir=',
                                          'id=',
                                          'installdir='
                                          'interactive',
                                          'no-iternactive',
                                          'name=',
                                          'root='
                                          'savegame-name=',
                                          'steam=',
                                          'variable=',
                                          'remove-variable=',
                                      ])
        except getopt.GetoptError as err:
            raise error.InvalidOptionError(err.msg)
        
        if (len(args) < 1):
            raise error.OptionError("pysgbackup-command \"{}\" has no GameID given!".format(cmd))
        elif (len(args) > 1):
            raise error.OptionError("pysgbackup-command \"{}\" takes only one GameID!".format(cmd))
        
        if (not self.application.games.has_game(args[0])):
            raise error.OptionError("Unknown GameID \"{}\"!".format(args[0]))
        
        options = GameOptions(self.application,cmd,
                              game=self.application.games.get(args[0]),
                              interactive=self.application.config.get_boolean('commandGame','editGameInteractive',True))
        
        for o,a in opts:
            if o in ('-i','--interactive'):
                options.interactive = True
            elif o in ('-I','--no-interactive'):
                options.interactive = False
            elif o in ('-g','--id'):
                options.game_id = a
            elif o in ('-n','--name'):
                options.game_name = a
            elif o in ('-N','--savegame-name'):
                options.savegame_name = a
            elif o in ('-r','--root'):
                options.savegame_root = a
            elif o in ('-d','--dir'):
                options.savegame_dir = a
            elif o in ('-x','--installdir'):
                options.installdir = a
            elif o in ('-s','--steam'):
                try:
                    options.steam_appid = abs(int(a))
                except:
                    raise error.OptionError('Steam Appid is not an integer value!')
            elif (o in ('-V','--variable')):
                if ('=' in o):
                    vname,vvalue = o.split('=',1)
                else:
                    vname = o
                    vvalue = ""
                options.add_variable(vname,vvalue)
            elif (o in ('-R','--remove-variable')):
                options.remove_variable(o)
    
        return options
    
    def edit_game_interactive(self,options:GameOptions):
        def get_edit_variables():
            edit = ""
            while edit.lower() not in ('a','e','s','n'):
                edit = input("Edit Variables? [A]dd/[D]elete/[E]dit/[S]how/[N]o: ")

            return edit
        # get_edit_variables()

        edit_done = False
        while not edit_done:
            print(("=" * 80) + "\n= Edit Game\n" + ("=" * 80))
            gid = input("Game ID [{}]: ".format(options.game_id))
            if (len(gid) > 0):
                options.game_id = gid
            
            name = input("Game name [{}]: ".format(options.game_name))
            if (len(name) > 0):
                options.game_name = name

            if options.savegame_name:
                sgname_default = options.savegame_name
            else:
                sgname_default = options.game_id

            sgname = input("Savegame Name [{}]: ".format(sgname_default))
            if len(sgname) > 1:
                options.savegame_name = sgname
            else:
                options.savegame_name = sgname_default

            sgroot = input("Savegame root-dir [{}]: ".format(options.savegame_root))
            if len(sgroot) > 0:
                options.savegame_root = sgroot

            sgdir = input("Savegame directory [{}]: ".format(options.savegame_dir))
            if len(sgdir) > 0:
                options.savegame_dir = sgdir

            installdir = input("Game installdir [{}]: ".format(options.installdir))
            if (len(installdir)) > 0:
                if (installdir == ":delete:"):
                    options.installdir = ""
                else:
                    options.installdir = installdir

            steam_appid_is_valid = False
            while not steam_appid_is_valid:
                steam_appid = input("Steam AppID [{}]: ".format(options.steam_appid))
                if not steam_appid:
                    steam_appid_is_valid = True
                else:
                    try:
                        options.steam_appid = abs(int(steam_appid))
                        steam_appid_is_valid = True
                    except:
                        steam_appid_is_valid = False

            edit_variables = get_edit_variables()
            while edit_variables.lower() != 'n':
                while edit_variables.lower() in ('a','e','s'):
                    if (edit_variables.lower() == 'a'):
                        vname = ""
                        while not vname:
                            vname = input("Variable: ")
                        vvalue = input("Value: ")
                        options.add_variable(vname,vvalue)
                        edit_variables = get_edit_variables()
                    elif (edit_variables.lower() == 'd'):
                        count = 0
                        vars = {}
                        for var,value in options.variables.items():
                            count += 1
                            vars[count] = (var,value)

                        for id,v in vars.items():
                            print("{}\t{}={}".format(id,v[0],v[1]))

                        var_ok = False
                        while not var_ok:
                            try:
                                variable = int(input("Select variable ([0] to abort): "))
                                if variable == 0:
                                    var_ok = True
                                    break
                                if variable in vars:
                                    options.remove_variable(vars[variable][0])
                                    var_ok = True
                            except:
                                pass
                        edit_variables = get_edit_variables()
                    
                    elif (edit_variables.lower() == 'e'):
                        count = 0
                        vars = {}
                        for var,value in options.variables.items():
                            count += 1
                            vars[count] = (var,value)

                        for count,v in vars.items():
                            print ("{}\t{}={}".format(count,v[0],v[1]))

                        var_ok = False
                        while not var_ok:
                            try:
                                variable = int(input("Select Variable ([0] to abort): "))
                                if variable == 0:
                                    break
                                if variable in vars:
                                    var_name = vars[variable][0]
                                    var_value = vars[variable][1]

                                    vname = input("Variable [{}]: ".format(var_name))
                                    if not vname:
                                        vname = var_name
                                    
                                    vvalue = input("Value [{}]: ".format(var_value))
                                    if not vvalue:
                                        vvalue = var_value
                                    else:
                                        if vvalue == ':delete:':
                                            vvalue = ""

                                    if vname != var_name:
                                        options.remove_variable(var_name)
                                    options.variables[vname] = vvalue
                                    var_ok = True
                            except:
                                pass
                        edit_variables = get_edit_variables()
                    elif (edit_variables.lower() == 's'):
                        for var,value in options.variables:
                            print("{}={}".format(var,value))
                        edit_variables = get_edit_variables()

            if not options.is_valid:
                print("Settings are not valid! Restarting edit!")
                continue

            print(("-"*80) + "\n" + "Game Settings:")
            game_settings=[
                ("Game ID:",options.game_id),
                ("Game name:",options.game_name),
                ("Savegame name:",options.savegame_name),
                ("Savegame root:",options.savegame_root),
                ("Savegame dir:",options.savegame_dir),
                ("Game installdir:",options.installdir),
                ("Steam AppID:",str(options.steam_appid))
            ]

            name_len = 0
            for name,value in game_settings:
                if len(name) > name_len:
                    name_len = len(name)

            name_len += 1

            for name,value in game_settings:
                print (name + (" " * (name_len - len(name))) + value)
            print("VARIABLES:")
            for var,value in options.variables.values():
                print("  {}={}".format(var,value))

            print("\n")
            ok = ""
            while (ok.lower() not in ('y','n')):
                ok = input("Does this seem reasonable? [Y]es/[N]o: ")
            
            if ok.lower() == 'y':
                edit_done = True
                return True
        return False

    def do_execute(self,options:GameOptions):
        if options.interactive:
            self.edit_game_interactive(options)

        if options.is_valid:
            old_id = options.game.game_id
            gameconf_file = options.game.gameconf_filename    
            game = options.update_game()
            if (gameconf_file != game.gameconf_filename):
                os.rename(gameconf_file,game.gameconf_filename)
            game.save()

            if (self.application.config.verbose):
                if (game.game_id != old_id):
                    print("Game {old_id}->{new_id}: \"{name}\" successfully edited!".format(
                        old_id=old_id,new_id=game.id,name=game.name))
                else:
                    print("Game {id}: \"{name}\" succesfully edited!".format(id=game.game_id,name=game.name))
            return 0
        
        print("Editing game {id}: \"{name}\" failed!".format(id=game.game_id,name=game.name),file=sys.stderr)
        return 1
# EditGame class

class RemoveGameOptions(CommandOptions):
    OPTION_ID = 'remove-game'

    def __init__(self,app,command,backup=True):
        CommandOptions.__init__(self,app,self.OPTION_ID,command)
        self.__game_ids = []
        self.__backup = backup

    @property
    def backup(self):
        return self.__backup
    @backup.setter
    def backup(self,b:bool):
        self.__backup = b

    @property
    def game_ids(self):
        return self.__game_id
    
    def add(self,game_id):
        if game_id not in self.__game_ids:
            self.__game_ids.append(game_id)

    @property
    def is_valid(self):
        return (len(self.__game_ids) > 0)
# RemoveGameOptions class

class RemoveGame(Command):
    def __init__(self,app):
        Command.__init__(self,app,"remove-game","Remove game from list.")

    def get_synopsis(self,command=None):
        if command is None:
            command = self.id

        return """sgbackup {command} [-Bb] [--backup] [--no-backup] <GameID>""".format(command=command)
    
    def get_help(self,command):
        if command is None:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)
    
    def do_parse(self,cmd,argv):
        try:
            opts,args = getopt.getopt(argv,'Bb',['--backup','--no-backup'])
        except getopt.GetoptError as err:
            raise error.OptionError("Illegal options for command \"{command}\"! ({msg})".format(command=cmd,msg=err.msg))
        
        if len(args) < 1:
            raise error.OptionError("Command \"{command}\" needs atleast one GameID as argument!".format(command=cmd))
        
        options = RemoveGameOptions(
            self.application,
            cmd,
            backup=self.application.config.get_boolean('commandGame','removeGameBackup',True))

        for o,a in opts:
            if o in ('-b','--backup'):
                options.backup=True
            elif o in ('-B','--no-backup'):
                options.backup=False

        for i in args:
            if self.application.games.has_game(i):
                options.add(i)
            else:
                raise error.OptionError("No game with id \"{id}\" found!".format(id=i))
            
        return options

    def do_execute(self, options:RemoveGameOptions):
        for gid in options.game_ids:
            try:
                game = self.application.games.get(gid)
            except:
                continue

            gcf = game.gameconf_filename
            if os.path.isfile(gcf):
                if options.backup:
                    if os.path.exists('.'.join((gcf,'backup'))):
                        count = 0
                        while os.path.exists('.'.join((gcf,'backup',count))):
                            count += 1
                        os.rename(gcf,'.'.join((gcf,'backup',count)))
                    else:
                        os.rename(gcf,'.'.join((gcf,'backup')))
                else:
                    os.unlink(gcf)

                self.application.games.remove(game.game_id)
                game.destroy()
        return 0
# RemoveGame class

class ListGamesOptions(CommandOptions):
    OPTIONS_ID = 'list-games'

    def __init__(self,app,command):
        CommandOptions.__init__(self,app,self.OPTIONS_ID,command)
        self.__show_all = True
        self.__show_finished = False
        self.__show_active = False

    @property
    def show_all(self):
        if self.__show_all:
            return True
        return (self.show_active and self.show_finished)
    
    @show_all.setter
    def show_all(self,b:bool):
        self.__show_all = b

    @property
    def show_finished(self):
        if self.__show_all:
            return True
        return self.__show_finished
    @show_finished.setter
    def show_finished(self,b:bool):
        self.__show_finished = b

    @property
    def show_active(self):
        if self.__show_all:
            return True
        return self.__show_active
    @show_active.setter
    def show_active(self,b:bool):
        self.__show_active = b

class ListGames(Command):
    def __init__(self,app,command='list-games',description="List games."):
        Command.__init__(self,app,command,description)

    def get_synopsis(self, command=None):
        if command is None:
            command = self.id

        return "sgbackup {command} [-af] [--active|--finished]".format(command=command)
    
    def get_help(self,command=None):
        if command is None:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)
        
    def do_parse(self, cmd, argv):
        try:
            opts,args = getopt.getopt(argv,'af',['active','finished'])
        except getopt.GetoptError as err:
            raise error.OptionError("Illegal option for command \"{command}\" given! ({message})".format(command=cmd,message=err.msg))
        
        options = ListGamesOptions(self.application,cmd)
        for o,a in opts:
            if o in ('-a','--active'):
                options.show_all = False
                options.show_active = True
            elif o in ('-f','--finished'):
                options.show_all = False
                options.show_finished = True
    
        if (len(args) > 0):
            raise error.OptionError('Command \"{command}\" does not take any arguments!'.format(command=cmd))
        
        return options
    
    def do_execute(self, options:ListGamesOptions):
        if options.show_all:
            game_ids = self.application.games.game_ids
        elif options.show_active:
            game_ids = self.application.games.active_game_ids
        elif options.show_finished:
            game_ids = self.application.games.finished_game_ids
        else:
            game_ids = self.application.games.game_ids

        gid_len = 0
        for gid in game_ids:
            if len(gid) > gid_len:
                gid_len = len(gid)

        gid_len = (((gid_len // 4) + 1) * 4)

        for gid in game_ids:
            try:
                game = self.application.games.get(gid)
                print("{}{}{}".format(gid,' ' * (gid_len - len(gid)),game.game_name))
            except:
                pass

        return 0
# ListGames class

class ListActiveGames(ListGames):
    def __init__(self,app):
        ListGames.__init__(self,app,"list-active-games","List active games.")

    def get_synopsis(self, command=None):
        if not command:
            command = self.id

        return "sgbackup {command}".format(command=command)
    
    def get_help(self,command=None):
        if not command:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)

    def do_parse(self,cmd,argv):
        if len(argv) > 0:
            raise error.OptionError("Command \"{command}\" does not take any options and arguments!".format(command=cmd))
        return ListGames.do_parse(self,cmd,['--active'])
# ListActiveGames class

class ListFinishedGames(ListGames):
    def __init__(self,app):
        ListGames.__init__(self,app,"list-finished-games","List finished games.")

    def get_synopsis(self, command=None):
        if not command:
            command = self.id

        return "sgbackup {command}".format(command=command)
    
    def get_help(self,command=None):
        if not command:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)

    def do_parse(self, cmd, argv):
        if len(argv) > 0:
            raise error.OptionError("Command \"{command}\" does not take any options and arguments!".format(command=cmd))
        return ListGames.do_parse(self,cmd,['--finished'])    
# ListFinishedGames class

class ActivateGameOptions(CommandOptions):
    def __init__(self,app,command):
        CommandOptions.__init__(self,app,'activate-game',command)
        self.__game_ids = []

    @property
    def game_ids(self):
        return self.__game_ids
    
    @property
    def games(self):
        games=[]
        for gid in self.game_ids:
            if self.application.games.has_game(gid):
                games.append(self.application.games.get(gid))
        return games
    
    def add(self,game_id:str):
        if game_id not in self.__game_ids and self.application.games.has_game(game_id):
            self.__game_ids.append(game_id)

    def remove(self,game_id:str):
        if game_id in self.game_ids:
            for i in range(self.__game_ids):
                if game_id == self.__game_ids[i]:
                    del self.__game_ids[i]
                    break

class ActivateGame(Command):
    def __init__(self, app):
        Command.__init__(self,app, 'activate-game', "Mark game active.")

    def get_synopsis(self, command=None):
        if command is None:
            command = self.id

        return "sgbackup {command} GAME_ID ...".format(command=command)
    
    def get_help(self,command=None):
        if command is None:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)
    
    def do_parse(self, cmd, argv):
        try:
            opts,args = getopt.getopt(argv,'',[])
        except getopt.GetoptError as err:
            raise error.OptionError("Illegal options for command \"{command}\"! ({message})".format(command=cmd,message=err.msg))
        
        if len(args) == 0:
            raise error.OptionError("Command \"{command}\" needs atleast one GameID!".format(command=cmd))
        
        options = ActivateGameOptions(self.application,cmd)

        for gid in args:
            if not self.application.games.has_game(gid):
                raise error.OptionError("Unknown GameID \"{game_id}\"!".format(game_id=gid))
            options.add(gid)

        return options

    
    def do_execute(self, options:ActivateGameOptions):
        for game in options.games:
            game.is_active = True
            game.save()
            if self.application.config.verbose:
                print("Game {id}: \"{name}\" set active.".format(id=game.game_id,name=game.name))

        return 0
# ActivateGame class

class FinishGameOptions(CommandOptions):
    def __init__(self,app,command):
        CommandOptions.__init__(self,app,'finish-game',command)
        self.__backup = self.application.config.get_boolean('commandGame','finishBackup',True)
        self.__game_ids = []

    @property
    def game_ids(self):
        return self.__game_ids
    
    @property
    def games(self):
        games = []
        for gid in self.__game_ids:
            if self.application.games.has_game(gid):
                games.append(self.application.games.get(gid))
        
        return games
    
    def add(self,game_id:str):
        if not game_id in self.__game_ids:
            self.__game_ids.append(game_id)

    def remove(self,game_id:str):
        if game_id in self.__game_ids:
            for i in range(len(self.__game_ids)):
                if self.__game_ids[i] == game_id:
                    del self.__game_ids[i]
                    break
    
    @property
    def backup(self):
        return self.__backup
    @backup.setter
    def backup(self,b:bool):
        self.__backup = b
# FinishGameOptions class

class FinishGame(Command):
    def __init__(self,app):
        Command.__init__(self,app,'finish-game',"Mark game as finished.")

    def get_synopsis(self,command=None):
        if command is None:
            command = self.id

        return "sgbackup {command} [-B | -b | --backup |--no-backup] GAME_ID ...".format(command=command)
    
    def get_help(self,command=None):
        if command is None:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)

    def do_parse(self, cmd, argv):
        try:
            opts,args = getopt.getopt(argv,'bB',['backup','no-backup'])
        except getopt.GetoptError as err:
            raise error.OptionError("Parsing options for command \"{command}\" failed! ({message})".format(command=cmd,message=err.msg))
        
        options = FinishGameOptions(self.application,cmd)

        for o,a in opts:
            if o in ('-b','--backup'):
                options.backup = True
            elif o in ('-B','--no-backup'):
                options.backup = False

        if (len(args) == 0):
            raise error.OptionError("Command \"{command}\" needs atleast on game id given!".format(command=cmd))
        
        for gid in args:
            if not self.application.games.has_game(gid):
                raise error.OptionError("Unknown GameID \"{game_id}\"!".format(game_id=gid))
            options.add(gid)

        return options
    
    def do_execute(self, options:FinishGameOptions):
        for game in options.games:
            game.is_finished = True
            game.save()
            if self.application.config.verbose:
                print("Game {id}: \"{name}\" marked as finished.".format(id=game.game_id,name=game.game_name))

            if options.backup:
                try:
                    game.backup()
                    if self.application.config.verbose:
                        print("Game {id}: \"{name}\" backup created.".format(id=game.game_id,name=game.game_name))
                except:
                    print("Game {id}: \"{name}\" backup failed!".format(id=game.game_id,name=game.name),file=sys.stderr)
                    return 1
        return 0
# FinishGame class

COMMANDS=[
    (AddGame,['add']),
    (EditGame,['edit']),
    (RemoveGame,['remove']),
    (ListGames,['list']),
    (ListActiveGames,['list-active','active']),
    (ListFinishedGames,['list-finished','finished']),
    (ActivateGame,['activate']),
    (FinishGame,['finish']),
]
