from ..command import Command,CommandOptions
from ..game import Game
from .. import error
from ..help import get_builtin_help
import os
import sys
import getopt
import subprocess

class BackupGameOptions(CommandOptions):
    def __init__(self,app,cmd):
        CommandOptions.__init__(self,app,'backup-game',cmd)

        self.__games = []

    @property
    def games(self):
        return self.__games
    
    def add_game(self,game:Game):
        if game not in self.__games:
            self.__games.append(game)

    def add_finished_games(self):
        for game in self.application.games.finished_games:
            self.add_game(game)

    def add_active_games(self):
        for game in self.application.games.active_games:
            self.add_game(game)

    def add_all_games(self):
        for game in self.application.games.games:
            self.add_game(game)

    def remove(self,game):
        if (isinstance(game,str)):
            for i in range(len(self.__games)):
                if self.__games[i].game_id == game:
                    del self.__games[i]
                    break
        elif (isinstance(game,Game)):
            if game in self.__games:
                for i in range(len(self.__games)):
                    if self.__games[i] == game:
                        del self.__games[i]
                        break
        else:
            raise TypeError("\"game\" needs to be a GameID string or a sgbackup.game.Game instance!")
        
class BackupGame(Command):
    def __init__(self,app):
        
        Command.__init__(self,app,'backup-game','Backup games.')

    def get_synopsis(self,command=None):
        if command is None:
            command = self.id

        return """sgbackup {command} [-aAf] [--active] [--all] [--finished] [GameID] ...""".format(command=command)
    
    def get_help(self,command=None):
        if command is None:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)
        
    
    def parse_vfunc(self, cmd, argv):
        try:
            opts,args = getopt.getopt(argv,'aAf',['all','active','finished'])
        except getopt.GetoptError as err:
            raise error.OptionError("Parsing options failed! ({error})".format(error=err.msg))
        
        options = BackupGameOptions(self.application,cmd)
        for o,a in opts:
            if (o in ['-a','--active']):
                options.add_active_games()
            elif (o in ['-A','--all']):
                options.add_all_games()
            elif (o in ['-f','--finished']):
                options.add_finished_games()
        
        for gid in args:
            if not gid in self.application.games.game_ids:
                raise error.OptionError("\"{game_id}\" is not a valid GameID!".format(game_id=gid))
            options.add_game(self.application.games.get(gid))

        return options
    
    def execute_vfunc(self, options):
        for game in options.games:
            if self.application.config.verbose:
                print("Backing up {game_id}: \"{game_name}\"".format(game_id=game.game_id,game_name=game.game_name))
            game.backup()


class RestoreGameOptions(CommandOptions):
    def __init__(self,app,cmd):
        CommandOptions.__init__(self,app,'restore-game',cmd)
    
        self.__game = None
        self.__backup_file = ""
        self.__choose = True

    @property
    def game(self):
        return self.__game
    @game.setter
    def game(self,game:Game):
        self.__game = game

    @property
    def backup_file(self):
        return self.__backup_file
    @backup_file.setter
    def backup_file(self,fn:str):
        self.__backup_file = fn

    @property
    def choose(self):
        return self.__choose
    @choose.setter
    def choose(self,b:bool):
        self.__choose = b

class RestoreGame(Command):
    def __init__(self,app):
        Command.__init__(self,app,'restore-game','Restore a game backup')

    def get_synopsis(self,command=None):
        if command is None:
            command = self.id
        return """sgbackup {command} <-a|-c|-f|-l|--choose|--latest|--latest-active|--latest-finished> GAME_ID
sgbackup {command} GAME_ID BACKUP_FILE""".format(command=command)
    
    def get_help(self,command=None):
        if command is None:
            command = self.id
        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)
    
    def parse_vfunc(self,cmd,argv):
        try:
            opts,args = getopt.getopt(argv,['acfl'],['choose','latest-active','latest-finished','latest'])
        except getopt.GetoptError as err:
            raise error.OptionError("Illegal options for command {command}! ({message})".format(command=cmd,message=err.msg))
        
        (BACKUP_LATEST,BACKUP_LATEST_ACTIVE,BACKUP_LATEST_FINISHED,BACKUP_SELECTED,BACKUP_CHOOSE) = range(5)
        selected = BACKUP_CHOOSE
        backup = ""
        for o,a in opts:
            if (o in ['-l','--latest']):
                selected = BACKUP_LATEST
            elif (o in ['-a','--latest-active']):
                selected = BACKUP_LATEST_ACTIVE
            elif (o in ['-c','--choose']):
                selected = BACKUP_CHOOSE
            elif (o in ['-f','--latest-finished']):
                selected = BACKUP_LATEST_FINISHED
        
        if len(args) == 0:
            raise error.OptionError("Missing GameID for command \"{command}\"!".format(command=cmd))
        
        options = RestoreGameOptions(self.application,cmd)

        if not self.application.games.has_game(args[0]):
            raise error.OptionError("No game with GameID \"{gameid}\" found!".format(gameid=args[0]))
        options.game = self.application.games.get(args[0])
        
        backup_file=None

        if selected == BACKUP_LATEST:
            backup_file = options.game.latest_backup
        elif selected == BACKUP_LATEST_FINISHED:
            backup_file = options.game.latest_finished_backup
        elif selected == BACKUP_LATEST_ACTIVE:
            backup_file == options.game.latest_active_backup

        if backup_file:
            options.backup_file = backup_file
            options.choose = False

        if len(args) >= 2:
            selected = BACKUP_SELECTED
            if (os.path.isabs(args[1])):
                if not os.path.isfile(args[1]):
                    raise error.OptionError("Backup \"{filename}\" does not exist!".format(filename=args[1]))
                options.backup_file = args[1]
                options.choose = False
            else:
                backup_found = False
                for bn,backup in ((os.path.basename(i),i) for i in options.game.backups):
                    if bn == args[1]:
                        backup_found=True
                        options.backup_file = backup
                        options.choose = False
                        break

                if not backup_found:
                    raise error.OptionError(
                        "No such backup \"{filename}\" for gane \"{gameid}\"!".format(
                            filename=args[1],gameid=options.game.game_id))

        return options
    
    def choose_backup(self,game:Game):
        def print_backups(title:str,map:dict):
            s = "title" + "\n"
            for key in sorted(map.keys()):
                s += "  [{id}]\t{backup}\n".format(id=key,backup=map[key])

            if sys.stdout.isatty:
                process = subprocess.Popen(self.application.config.pager,stdin=subprocess.PIPE)
                process.stdin.write(s.encode('utf-8'))
                process.communicate()
            else:
                print(s,end='')

        if not game.backups:
            print("Game \"{game}\" has no backups! Skipping!".format(game=game.game_name))
            return None

        print("SaveGame backups for {game}:".format(game=str(game.game_name)))
        choose = "select"
        while (choose != 'done'):
            if (choose == 'select'):
                ok = False
                while (not ok):
                    x = input("Select Backups:\n\t[A]  Active Backups\n\t[F]  Finished Backups\n\t[X]  All Backups\n\t[Q]  Quit\n>> ")
                    if (x.lower() in ['a','active']):
                        choose = 'active'
                        ok = True
                    elif (x.lower() in ['f','finished']):
                        choose = 'finished'
                        ok = True
                    elif (x.lower() in ['x','all']):
                        choose = 'all'
                        ok = True
                    elif (x.lower() in ['q','quit']):
                        return None
                    
            if (choose == 'active'):
                ok = False
                sgb_map = {}
                i=1
                title = 'Active SaveGame Backups:'
                backups = game.active_backups
                if not backups:
                    return None
                backups = sorted(backups,reverse=True)
                
                sgb_map[i] = game.latest_active_backup
                
                for b in backups:
                    if b in sgb_map.values():
                        continue
                    i += 1
                    sgb_map[i] = b

                print_backups(title,sgb_map)

                while (not ok):
                    x = input("Choose a backup to restore or [A]ctive|[X] all|[F]inished|[Q]uit:")
                    if x.isnumeric():
                        try:
                            return sgb_map[int(x)]
                        except:
                            continue
                    elif (x.lower() in ['a','active']):
                        choose = 'active'
                        ok=True
                    elif (x.lower() in ['f','finished']):
                        choose = 'finished'
                        ok = True
                    elif (x.lower() in ['x','all']):
                        choose = 'all'
                        ok=True
                    elif (x.lower() in ['q','quit']):
                        return None
                    
            elif (choose == 'all'):
                sgb_map = {}
                i = 1
                title = "All SaveGame Backups:"
                backups = game.backups
                if not backups:
                    return None
                
                sgb_map[i] = game.latest_backup
                for b in backups:
                    if b in sgb_map.values():
                        continue

                    i += 1
                    sgb_map[i] = b
                    
                print_backups(title,sgb_map)

                ok = False
                while (not ok):
                    x = input("Choose a backup to restore or [A]ctive|[X] all|[F]inished|[Q]uit:")
                    if x.isnumeric():
                        try:
                            return sgb_map[int(x)]
                        except:
                            continue
                    elif (x.lower() in ['a','active']):
                        choose = 'active'
                        ok=True
                    elif (x.lower() in ['f','finished']):
                        choose = 'finished'
                        ok = True
                    elif (x.lower() in ['x','all']):
                        choose = 'all'
                        ok=True
                    elif (x.lower() in ['q','quit']):
                        return None
            elif (choose == 'finished'):
                ok = False
                sgb_map = {}
                i = 1
                title = "Finished SaveGame Backups"
                backups = game.finished_backups
                if not backups:
                    return None
                backups = sorted(backups,reverse=True)
                sgb_map[i] = game.latest_finished_backup
                
                for b in backups:
                    if b in sgb_map.values():
                        continue

                    i += 1
                    sgb_map[i] = b
                    
                print(title,sgb_map)

                ok = False
                while (not ok):
                    x = input("Choose a backup to restore or [A]ctive|[X] all|[F]inished|[Q]uit:")
                    if x.isnumeric():
                        try:
                            return sgb_map[int(x)]
                        except:
                            continue
                    elif (x.lower() in ['a','active']):
                        choose = 'active'
                        ok=True
                    elif (x.lower() in ['f','finished']):
                        choose = 'finished'
                        ok = True
                    elif (x.lower() in ['x','all']):
                        choose = 'all'
                        ok=True
                    elif (x.lower() in ['q','quit']):
                        return None
            else:
                choose = 'select'
        return None

    def execute_vfunc(self,options:RestoreGameOptions):
        if options.choose:
            bf = self.choose_backup(options.game)
            if bf is not None:
                options.backup_file = bf
        
        if not options.backup_file:
            print("No backup file selected! Skipping!",file=sys.stderr)
            return 0
        
        try:
            options.game.restore(options.backup_file)
        except Exception as err:
            print("Restoring backup for game \"{game}\" failed! ({message})".format(game=options.game.game_name,message=err.args[0]),
                  file=sys.stderr)
            return 1


COMMANDS=[
    (BackupGame,('backup',)),
    (RestoreGame,('restore',)),
]
