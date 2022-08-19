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

class BackupDialog(Gtk.Dialog):
    def __init__(self,parent=None):
        Gtk.Dialog.__init__(self,parent=parent)
        self.__games = []
        self.__cancel = False
        
        self.set_title('PySGBackup: Backup Savegames')

        vbox = self.get_content_area()        
        
        self.label = Gtk.Label()
        self.label.set_markup(self._get_label_markup())
        vbox.pack_start(self.label,False,False,5)
            
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,0)    
        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        vbox.pack_start(self.progress,False,False,0)
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,0)
        
        self.button_cancel = Gtk.Button('Cancel')
        self.button_cancel.connect('clicked',self._on_button_cancel_clicked)
        self.get_action_area().pack_start(self.button_cancel,False,False,0)
        self.get_action_area().set_child_secondary(self.button_cancel,True)
        
        self.button_close = self.add_button('Close',Gtk.ResponseType.CLOSE)
        self.show_all()
        
    @property
    def games(self):
        return self.__games
        
    def add_game(self,game):
        for g in self.games:
            if g.game_id == game.game_id:
                return
                
        self.games.append(game)
        self.label.set_markup(self._get_label_markup())
        self.button_close.set_sensitive(False)
        
    def _get_label_markup(self):
        markup = '<span size="large">'
        
        if len(self.games) == 1:
            markup += 'Backing up 1 game'
        else:
             markup += 'Backing up {0} games.'.format(len(self.games))
             
        markup += '</span>'
        return markup
        
    def _on_button_cancel_clicked(self,button):
        self.__cancel=True
        button.set_sensitive(False)
        
    def _on_thread_update(self,data):
        text = "Backing up: {0}".format(data['game'].name)
        self.progress.set_text(text)
        self.progress.set_fraction(data['fraction'])
        self.progress.show()
        
        
    def _on_thread_finished(self):
        if self.__cancel:
            self.progress.set_text('Backup Canceled')
        else:
            self.progress.set_text('Backups finished')
            self.progress.set_fraction(1.0)
            
        self.button_cancel.set_sensitive(False)
        self.button_close.set_sensitive(True)
        
    def _thread_func(self):
        count = 0
        games = list(self.games)
        
        if not games:
            GLib.idle_add(self._on_thread_finished)
            return
        
        db = sgbackup.database.Database()
        
        for g in games:
            if self.__cancel:
                GLib.idle_add(self._on_thread_finished)
                return
        
            data = {'game': g, 'fraction': (count/len(games))}
            GLib.idle_add(self._on_thread_update,data)
            sgbackup.backup.backup(db,g)
            count += 1
            
        GLib.idle_add(self._on_thread_finished)
    
    def run(self):
        self.button_close.set_sensitive(False)
        
        thread = threading.Thread(target=self._thread_func)
        thread.daemon = True
        thread.start()
        return Gtk.Dialog.run(self)
# BackupDialog class

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
    (FAILED_IGNORE,FAILED_DELETE) = range(2)
    (MISSING_IGNORE,MISSING_CREATE,MISSING_DELETE) = range(3)
    
    def __init__(self,games=[],parent=None):
        Gtk.Dialog.__init__(self)
        self.__games=[]
        self.__action_failed = self.FAILED_IGNORE
        self.__action_missing = self.MISSING_IGNORE
        
        for i in games:
            self.add_game(i)
        
        vbox=self.get_content_area()
        
        label = Gtk.Label()
        label.set_markup('<span size="large">' 
                         + 'Checking checksums for SaveGame-backups'
                         + '</span>')
        vbox.pack_start(label,True,True,0)
        
        
        failed_actions = [
            ('ignore', 'Ignore files where checksum-test failed.'),
            ('delete', 'Delete files where checksum-test failed.')
        ]
        
        self.sizegroup = Gtk.SizeGroup()
        self.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
        
        hbox= Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = Gtk.Label('Failed checksum action:')
        self.sizegroup.add_widget(label)
        hbox.pack_start(label,False,False,5)
        self.failed_cbox = Gtk.ComboBoxText()
        for id,text in failed_actions:
            self.failed_cbox.append(id,text)
        self.failed_cbox.set_active_id('delete')
        hbox.pack_start(self.failed_cbox,True,True,0)
        vbox.pack_start(hbox,False,False,0)
        
        missing_actions = [
            ('ignore','Ignore files where checksums are missing.'),
            ('create', 'Create missing checksums.'),
            ('delete', 'Delete Files where checksums are missing.')
        ]
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = Gtk.Label('Missing checksum action:')
        self.sizegroup.add_widget(label)
        hbox.pack_start(label,False,False,5)       
        self.missing_cbox = Gtk.ComboBoxText()
        for id,text in missing_actions:
            self.missing_cbox.append(id,text)
        self.missing_cbox.set_active_id('create')
        hbox.pack_start(self.missing_cbox,True,True,0)
        self.vbox.pack_start(hbox,False,False,0)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        vbox.pack_start(separator,False,False,5)
        
        self.progress = Gtk.ProgressBar()
        self.progress.set_text('Checking checksums')
        vbox.pack_start(self.progress,False,False,0)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        vbox.pack_start(separator,False,False,5)
        
        buttonbox = self.get_action_area()
        self.button_run = Gtk.Button('Run')
        self.button_run.connect('clicked',self._on_button_run_clicked)
        buttonbox.pack_start(self.button_run,False,False,0)
        buttonbox.set_child_secondary(self.button_run,True)
        
        self.button_close = self.add_button('Close',Gtk.ResponseType.CLOSE)
        self.button_close.set_sensitive(True)
        
        self.show_all()
    
    def get_missins_action(self):
        actions = {'ignore':self.MISSING_IGNORE,'delete':self.MISSING_DELETE,'create':self.MISSING_CREATE}
        return actions[self.missing_cbox.get_active_id()]
        
    def get_failed_action(self):
        actions={'ignore':self.FAILED_IGNORE,'delete':self.FAILED_DELETE}
        return actions[self.failed_cbox.get_active_id()]
        
    def _on_button_run_clicked(self,button):
        self.__action_failed = self.get_failed_action()
        self.__action_missing = self.get_missins_action()
        
        self.button_run.set_sensitive(False)
        self.button_close.set_sensitive(False)
        self.missing_cbox.set_sensitive(False)
        self.failed_cbox.set_sensitive(False)
        
        self.__thread = threading.Thread(target=self._thread_func)
        self.__thread.set_daemon = True
        self.__thread.start()
                
        
    @property
    def games(self):
        return self.__games
        
    def add_game(self,game):
        db = sgbackup.database.Database()
        if isinstance(game,str):
            g = db.get_game(game)
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
        self.progress.set_fraction(data['fraction'])
        if 'text' in data:
            text = data['text']
        else:
            text = '[{}] {}'.format(data['file']['game'].name,data['file']['basename'])
        self.progress.set_text(text)
        self.progress.show()
        
    def _on_thread_finished(self):
        self.progress.set_fraction(1.0)
        self.progress.set_text('DONE')
        self.button_close.set_sensitive(True)
        self.button_run.set_sensitive(True)
        self.failed_cbox.set_sensitive(True)
        self.missing_cbox.set_sensitive(True)
        self.show_all()
        
    def _thread_func(self):
        db = sgbackup.database.Database()
        missing_action = self.get_missins_action()
        failed_action = self.get_failed_action()
        files = []
        count = 0
        data = {'fraction':0.0,'text': 'Creating file-list'}
        GLib.idle_add(self._on_thread_update,data)
        
        for g in self.games:
            for i in sgbackup.backup.find_backups(g):
                files.append({'game':g,'filename': i,'basename':os.path.basename(i)})
            
        steps = (len(files) + 1)
        count=1    
        for f in files:
            data = {
                'fraction': (count/steps),
                'file': f
            }
            GLib.idle_add(self._on_thread_update,data)
            count += 1
            
            dbfile = db.get_game_backup(f['game'],f['basename'])
            if not dbfile:
                if missing_action == self.MISSING_IGNORE:
                    continue
                elif missing_action == self.MISSING_DELETE:
                    sgbackup.backup.delete_backup(db,f['filename'])
                elif missing_action == self.MISSING_CREATE:
                    cksum = CONFIG['backup.checksum']
                    h = hashlib.new(cksum)
                    with open(f['filename'],'rb') as ifile:
                        h.update(ifile.read())
                    db.add_game_backup(f['game'],f['basename'],cksum,h.hexdigest())
                else:
                    raise RuntimeError('should not be reached!')
                continue
            
            h = hashlib.new(dbfile['checksum'])
            with open(f['filename'],'rb') as ifile:
                h.update(ifile.read())
            if h.hexdigest() != dbfile['hash']:
                if failed_action == self.FAILED_IGNORE:
                    continue
                elif failed_action == self.FAILED_DELETE:
                    sgbackup.backup.delete_backup(f['game'],f['filename'])
                else:
                    raise RuntimeError('should not be reached')
        GLib.idle_add(self._on_thread_finished)
    # _thread_func()
    
# CheckGamesDialog class
     
