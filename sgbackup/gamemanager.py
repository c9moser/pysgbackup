# -*- coding: utf-8 -*-
# Author: Chrstian Moser
# License: GPL
# File: sgbackup/gamemanager.py
# Module: sgbackup.gamemanager

from gi.repository import GObject,GLib
import sys
import os
from .game import Game

class GameManager(GObject.GObject):
    __name__ = "sgbackup.game.GameManager"
    __gsignals__ = {
        'add': (GObject.SIGNAL_RUN_FIRST,None,(Game,)),
        'remove': (GObject.SIGNAL_RUN_FIRST,None,(Game,)),
        'destroy': (GObject.SIGNAL_RUN_LAST,None,()),
    }

    def __init__(self):
        GObject.GObject.__init__(self)

        self.__games={}
        self.__steam_games={}
        self.__app = None

    def _real_initialize(self,app):
        self.__app = app
        self.__load_games()

    @GObject.Property
    def application(self):
        return self.__app
    
    @GObject.Property
    def is_initialized(self):
        return (self.__app is not None)
    
    def __load_games(self):
        for i in os.listdir(self.application.config.gameconf_dir):
            if i.endswith('.game'):
                try:
                    gc = GLib.KeyFile.new()
                    gc.load_from_file(os.path.join(self.application.config.gameconf_dir,i,),0)
                    game = Game.new_from_gameconf(self.application,gc)
                    if game.is_valid:
                        self.__games[game.game_id] = game
                        game._gamemanager_id_changed = game.connect('id-changed',self._on_game_id_changed)
                        if game.steam_appid:
                            self.__steam_games[game.steam_appid] = game
                            game._gamemanager_steam_appid_changed = game.connect('steam-appid-changed',self._on_steam_appid_changed)
                except Exception as err:
                    print("Unable to load gameconf \"{filename}\"! ({message})".format(
                            filename=os.path.join(self.application.config.gameconf_dir,i),
                            message=str(err)
                        ),
                        file=sys.stderr)
    # GameManager.__load_games()
        
    @GObject.Property
    def game_ids(self):
        gids=[]

        for i in self.__games.keys():
            gids.append(i)

        gids.sort()
        return gids
    
    @GObject.Property
    def games(self):
        return self.__games.values()
    
    @GObject.Property
    def steam_games(self):
        return self.__steam_games.values()
    
    @GObject.Property
    def steam_ids(self):
        return self.__steam_games.keys()
    
    @GObject.Property
    def steam_items(self):
        return dict(self.__steam_games).items()
    
    @GObject.Property
    def finished_game_ids(self):
        gids =  [gid for gid,game in self.__games.items() if game.is_finished]
        gids.sort()
        return gids
    
    @GObject.Property
    def finished_games(self):
        return [game for game in self.__games.values() if game.is_finished]
    
    @GObject.Property
    def active_game_ids(self):
        gids = [gid for gid,game in self.__games.items() if game.is_active]
        gids.sort()
        return gids
    
    @GObject.Property
    def active_games(self):
        return [game for game in self.__games.values() if game.is_active]
    
    def has_game(self,game_id:str):
        return (game_id in self.__games)
    
    def get(self,game_id:str):
        try:
            return self.__games[game_id]
        except:
            raise LookupError("Unable to lookup game with id \"{}\"!".format(game_id))
        
    def add(self,game:Game):
        if not game.is_valid:
            raise ValueError("Game instance is not valid!")
        self.emit('add',game)

    def do_add(self,game):
        self.__games[game.id] = game
        if not hasattr(game,'_gamemanager_id_changed'):
            game._gamemanager_id_changed = self.game.connect('id-changed',self._on_game_id_changed)

        if not hasattr(game,'_gamemanager_steam_appid_changed'):
            game._gamemanager_steam_appid_changed = self.game.connect('steam-appid-changed',self._on_steam_appid_changed)

        if game.steam_appid:
            self.__steam_games[game.steam_appid] = game
            

    def remove(self,game):
        if isinstance(game,Game):
            if game.id in self.__games:
                self.emit('remove',game)
        elif isinstance(game,str):
            if game in self.__games:
                self.emit('remove',self.__games[game])
    
    def do_remove(self,game):
        if game.id in self.__games:
            del self.__games[game.id]
        if hasattr(game,'_gamemanager_game_id_changed'):
            game.disconnect(game._gamemanager_id_changed)
            del game._gamemanager_id_changed
        

        if game.steam_appid and game.steam_appid in self.__steam_games:
            del self.__steam_games[game.steam_appid]
            
        if hasattr(game._gamemanager_steam_appid_changed):
            game.disconnect(game._gamemanager_steam_appid_changed)
            del game._gamemanager_steam_appid_changed
        game.destroy()

    def _on_game_id_changed(self,game,old_id):
        if old_id in self.__games:
            del self.__games[old_id]
        self.add(game)

    def _on_steam_appid_changed(self,game,old_appid):
        if (old_appid in self.__steam_games):
            del self.__steam_games[old_appid]
        if (game.steam_appid):
            self.__steam_games[game.steam_appid] = game

    def destroy(self):
        self.emit('destroy')

    def do_destroy(self):
        for gid,game in self.__games.items():
            game.destroy()
        
        self.__games = {}
        self.__app = None

#GameManager
