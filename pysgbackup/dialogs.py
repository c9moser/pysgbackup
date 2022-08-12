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
import shelve
import time
import hashlib

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
        vbox.pack_start(progress,False,False,0)
        
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
        return Gtk.Dialog.run(self)
# FinalBackupDialog

class UnfinalGameDialog(Gtk.Dialog):
    def __init__(self,game,parent=None):
        Gtk.Dialog.__init__(self,parent)
           
        self.game = game
        self.__thread_finished = False
        self.__missing_response = 0
        self.__failed_response = 0
        
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
        self.progress.set_text('DONE')
        self.button_close.set_sensitive(True)       
        
    def run(self):
        GLib.timeout_add(100, self._update_progress)
        thread = threading.Thread(target=self._thread_func)
        thread.daemon = True
        thread.start()
        
        return Gtk.Dialog.run(self)
# UnfinalGameDialog class

class CheckGamesDialog(Gtk.Dialog):
    def __init__(self,games=[],parent=None):
        Gtk.Dialog.__init__(self)
        self.__games=[]
        self.__response=0
        self.__cv = threading.Condition()
        
        for i in games:
            self.add_game(i)
        
        vbox=self.get_content_area()
        
        label = Gtk.Label()
        label.set_markup('<span size="large">' 
                         + 'Checking checksums for SaveGame-backups'
                         + '</span>')
        vbox.pack_start(label,True,True,0)
        
        self.progress = Gtk.ProgressBar()
        self.progress.set_text('Checking checksums')
        vbox.pack_start(self.progress,False,False,0)
        
        self.button_close = self.add_button('Close',Gtk.ResponseType.CLOSE)
        self.button_close.set_sensitive(False)
        
        self.show_all()
        
    @property
    def games(self):
        return self.__games
        
    def add_game(self,game):
        if isinstance(game,str):
            g = sgbackup.db.get_game(game)
        elif isinstance(game,sgbackup.games.Game):
            g = game
        else:
            raise TypeError('game')

        if g:
            game_found = False
            for i in self.__games:
                if i.game_id == g.game_id:
                    game_found = True
                    break
                
            if not game_found:
                self.__games.append(g)
    # add_game()
    
    def _on_thread_update(self,data):
        text = '<{}> {}'.format(data['game'].name,os.path.basename(data['filename']))
            
        self.progress.set_fraction(data['fraction'])
        self.progress.set_text(text)
        self.progress.show()
        
    def _on_thread_finished(self):
        self.progress.set_fraction(1.0)
        self.progress.set_text('DONE')
        self.button_close.set_sensitive(True)
        
    def _thread_func(self):
        (FAILED_NONE,FAILED_IGNORE,FAILED_DELETE) = range(3)
        (MISSING_NONE,MISSING_IGNORE,MISSING_CREATE,MISSING_DELETE) = range(4)
        
        def _get_action_failed(filename):
            with self.__cv:
                dialog = Gtk.MessageDialog(self,
                                           Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                           Gtk.MessageType.ERROR,
                                           Gtk.ButtonsType.NONE,
                                           'Checksum for filename "{0}" doeas not match!'.format(os.path.basename(filename)))
                dialog.format_secondary_markup('What do you want to do?')
                dialog.add_button('Ignore file',FAILED_IGNORE)
                dialog.add_button('Delete file',FAILED_DELETE)
                result = dialog.run()
                dialog.hide()
                dialog.destroy()
                if result == Gtk.ResponseType.DELETE_EVENT:
                    self.__response = FAILED_IGNORE
                else:
                    self.__response = result
                self.__cv.notify()
        # _get_action_failed()
        
        def _get_action_missing(filename):
            with self.__cv:
                dialog = Gtk.MessageDialog(self,
                                           Gtk.DialogFlags.DESTROY_WITH_PARENT, 
                                           Gtk.MessageType.ERROR,
                                           Gtk.ButtonsType.NONE,
                                           'Checksum for filename "{0}" not found!'.format(os.path.basename(filename)))
                dialog.format_secondary_markup('What do you want to do?')
                dialog.add_button('Ignore file',MISSING_IGNORE)
                dialog.add_button('Create missing checksum',MISSING_CREATE)
                dialog.add_button('Delete file',MISSING_DELETE)
                result = dialog.run()
                dialog.hide()
                dialog.destroy()
                if result == Gtk.ResponseType.DELETE_EVENT:
                    self.__response = MISSING_IGNORE
                else:
                    self.__response = result
                self.__cv.notify()
        # _get_action_missing()
        
        def _predicate():
            return (self.__response != 0)
            
        backup_dir = CONFIG['backup.dir']
        check_files = []
        for g in self.games:
            for f in sgbackup.backup.find_backups(g):
                check_files.append((g,f,'/'.join((g.savegame_name,os.path.dirname(f)))))
                
        x = len(check_files) + 1
        count=1
        with shelve.open(CONFIG['backup.checksum-database']) as d:
            for g,fn,cn in check_files:
                data = {
                    'fraction': (count/x),
                    'game': g,
                    'filename': fn
                }
                GLib.idle_add(self._on_thread_update,data)
                count += 1
                if cn in d.keys():
                    check = d[cn]
                    h = hashlib.new(check['algorithm'])
                    with open(fn,'rb') as ifile:
                        h.update(ifile.read())
                        
                    digest = h.hexdigest()
                    if check['hash'] != digest:
                        self.__response=FAILED_NONE
                        GLib.idle_add(_get_action_failed,fn)
                    
                        with self.__cv:
                            self.__cv.wait_for(_predicate)
                            result = self.__response
                        
                        if result == FAILED_IGNORE:
                            continue
                        elif result == FAILED_DELETE:
                            sgbackup.backup.delete_backup(g,fn)
                        else:
                            raise RuntimeError('Unknown response: {}'.format(self.__failed_response))
                    
                else:
                    self.__response = MISSING_NONE
                    GLib.idle_add(_get_action_missing,fn)
                    
                    with self.__cv:
                        self.__cv.wait_for(_predicate)
                        result = self.__response
                    
                    if result == MISSING_IGNORE:
                        continue
                    elif result == MISSING_DELETE:
                        sgbackup.delete_backup(g,filename)
                    elif result == MISSING_CREATE:
                        algorithm = CONFIG['backup.checksum']
                        h = hashlib.new(algorithm)
                        with open(fn,'rb') as ifile:
                            h.update(ifile.read())
                        d[cn]={'algorithm':algorithm, 'hash':h.hexdigest()}
                    else:
                        raise RuntimeError('Unknown response: {}'.format(self.__missing_response))
            
        GLib.idle_add(self._on_thread_finished)
    # _thread_func()
    
    def run(self):
        thread = threading.Thread(target=self._thread_func)
        thread.dameon = True
        thread.start()
                
        return Gtk.Dialog.run(self)
# CheckGamesDialog class
     
