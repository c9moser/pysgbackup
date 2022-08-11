#-*- coding:utf-8 -*-
################################################################################
# pysgbackup
#   Copyright (C) 2022,  Christian Moser
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
################################################################################

import gi
from gi.repository import Gtk,GLib,GObject

import threading
import sgbackup
from sgbackup.config import CONFIG
import pysgbackup

import sqlite3
import sys
import os

class FinalBackupDialog(Gtk.Dialog):
    def __init__(self,game,parent=None):
        Gtk.Dialog.__init__(self,parent)

        self.game = game
        self.__thread_finished = False
        
        self.set_title('PySGBackup: Create Final Backup')
        
        vbox = self.get_content_area()
        label = Gtk.Label()
        label.set_markup('<span size="large">' 
                         + 'Creating final backup for game "{0}".'.format(self.game.name)
                         + '</span>')
        vbox.pack_start(label,True,True,0)
        
        self.progress = Gtk.ProgressBar()
        self.progress.set_text(game.game_id)
        self.progress.set_pulse_step(0.1)
        
        self.button_close=self.add_button('Close',Gtk.ResponseType.CLOSE)
        self.button_close.set_sensitive(False)
        
        self.show_all()
    
    @property
    def game(self):
        return self.__game
        
    @game.setter
    def game(self,game):
        if isinstance(game,str):
            self.__game = sgbackup.db.get_game(game)
            if not self.__game:
                raise ValueError('"game" is not a valid GameID!')
        if isinstance(game,sgbackup.games.Game):
            self.__game = game
        else:
            raise TypeError('"game" needs to be an "sgbackup.games.Game" instance or a valid GameID!')
            

    @property
    def _thread_finished(self):
        return self.__thread_finished
        
    def _thread_func(self):
        if self.game:
            db = sgbackup.database.Database()
            self.game.final_backup = True
            db.add_game(self.game)
            sgbackup.backup.backup(self.game)
            
        GLib.idle_add(self._on_thread_finished)
        
    def _on_thread_finished(self):
        self.__thread_finished = True
        self.button_close.set_sensitive(True)
        
    def _update_progress(self):
        if self._thread_finished:
            self.progress.set_fraction(1.0)
            return False
            
        self.progress.pulse()
        return True
            
    def do_response(self,response):
        if response == Gtk.ResponseType.CLOSE:
            self.hide()
            self.destroy()
        
    def run(self):
        thread = threading.Thread(target=self._thread_func)
        thread.dameon = True
        GLib.timeout_add(100,self._update_progress)
        thread.start()
        return Gtk.Dialog.run()
# FinalBackupDialog

class UnfinalGameDialog(Gtk.Dialog):
    def __init__(self,game,parent=None):
        Gtk.Dialog.__init__(self,parent)
        
        
        self.game = game
        self.__thread_finished = False
        
        vbox = self.get_content_area()
        label = Gtk.Label()
        label.set_markup('<span size="large">' 
                         + 'Unfinal game "{0}".'.format(self.game.name) 
                         + '</span>')
        vbox.pack_start(label,True,True,0)
        self.progress = Gtk.ProgressBar()
        self.progress.set_text(game.name)
        self.progress.set_show_text(True)
        self.progress.set_pulse_step(0.05)
        self.vbox.pack_start(self.progress,False,False,0)
        self.button_close = self.add_button('Close', Gtk.ResponseType.CLOSE)
        self.button_close.set_sensitive(False)
        
        self.show_all()       
        
        
    @property
    def game(self):
        return self.__game
        
    @game.setter
    def game(self,g):
        if isinstance(g,str):
            self.__game = sgbackup.db.get_game(g)
            if not self.__game:
                raise ValueError('"game" is not a valid GameID!')
        elif isinstance(g,sgbackup.games.Game):
            self.__game = g
        else:
            raise TypeError('"game" needs to be an "sgbackup.games.Game" instance or a valid GameID!')
        
    @property
    def _thread_finished(self):
        return self.__thread_finished
        
    def _thread_func(self):
        self.__thread_finished = False
        try:
            db = sgbackup.database.Database()
            sgbackup.backup.unfinal(db,self.game)
        except Exception as error:
            print(error,file=sys.stderr)
            
        GLib.idle_add(self._on_thread_finished)
        
    def _update_progress(self):
        if self._thread_finished:
            self.progress.set_fraction(1.0)
            return False
            
        self.progress.pulse()
        return True
        
    def _on_thread_finished(self):
        self.__thread_finished = True
        self.button_close.set_sensitive(True)       
        
    def run(self):
        GLib.timeout_add(100, self._update_progress)
        thread = threading.Thread(target=self._thread_func)
        thread.daemon = True
        thread.start()
        
        return Gtk.Dialog.run(self)
# UnfinalGameDialog class

