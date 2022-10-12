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
from gi.repository import Gtk,Gdk,GLib,GObject

import threading
import sgbackup
from sgbackup.config import CONFIG
from . import utility
import pysgbackup

import sqlite3
import sys
import os
import shelve
import time
import hashlib
import configparser
import string
import subprocess

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
            try:
                sgbackup.backup.backup(db,g)
            except Exception as error:
                print(error,file=sys.stderr)
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
        vbox.pack_start(self.progress,False,False,0)
        
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
            sgbackup.backup.backup(db,self.game)
            
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

class CheckBackupDialog(Gtk.Dialog):
    (FAILED_IGNORE,FAILED_DELETE) = range(2)
    (MISSING_IGNORE,MISSING_CREATE,MISSING_DELETE) = range(3)
    
    def __init__(self,parent,game,files=[]):
        Gtk.Dialog.__init__(self,parent)
        self.game = game
        self.__files = files
        self.set_default_size(600,400)
        self.set_title('PySGBackup: Check Backups')
                
        vbox = self.get_content_area()
        label = Gtk.Label()
        label.set_markup('<span size="x-large">' + 'Checking game backup(s).' + '</span>')
        vbox.pack_start(label,False,False,0)
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL),False,False,5)
        
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,0)
        self.sizegroup = Gtk.SizeGroup()
        self.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
        
        failed_actions = [
            ('ignore', 'Ignore files where checksum-test failed.'),
            ('delete', 'Delete files where checksum-test failed.')
        ]
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = Gtk.Label('Failed checksum action:')
        self.sizegroup.add_widget(label)
        hbox.pack_start(label,False,False,5)
        self.failed_cbox = Gtk.ComboBoxText()
        for id,text in failed_actions:
            self.failed_cbox.append(id,text)
        self.failed_cbox.set_active_id('ignore')
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
        
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL),False,False,5)
        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        vbox.pack_start(self.progress,False,False,0)
        
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL),False,False,5)
        
        self.progressview_scrolled = Gtk.ScrolledWindow()
        buf = Gtk.TextBuffer()
        self.stdout_tag = buf.create_tag('stdout',foreground='green')
        self.stderr_tag = buf.create_tag('stderr',foreground='red')
        self.progressview = Gtk.TextView()
        self.progressview.set_buffer(buf)
        self.progressview_scrolled.add(self.progressview)
        vbox.pack_start(self.progressview_scrolled,True,True,0)
        
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL),False,False,5)
        
        buttonbox = self.get_action_area()
        self.button_run = Gtk.Button('Run')
        self.button_run.connect('clicked',self._on_button_run_clicked)
        buttonbox.pack_start(self.button_run,False,False,0)
        buttonbox.set_child_secondary(self.button_run,True)
        
        self.button_close = self.add_button('Close',Gtk.ResponseType.CLOSE)
        self.show_all()
        
    @property
    def game(self):
        return self.__game
        
    @game.setter
    def game(self,g):
        if not isinstance(g,sgbackup.games.Game):
            raise TypeError('"game" is not a sgbackup.games.Game instance!')
        
        if hasattr(self,'__game') and self.__game.game_id != g.game_id and self.__files:
            self.__files = []
        self.__game = g
        
    @property
    def files(self):
        return self.__files
        
    @property
    def missing_action(self):   
        actions = {'ignore':self.MISSING_IGNORE,'delete':self.MISSING_DELETE,'create':self.MISSING_CREATE}
        return actions[self.missing_cbox.get_active_id()]
        
    @property
    def failed_action(self):
        actions={'ignore':self.FAILED_IGNORE,'delete':self.FAILED_DELETE}
        return actions[self.failed_cbox.get_active_id()]
        
    def _on_button_run_clicked(self,button):
        self.button_run.set_sensitive(False)
        self.button_close.set_sensitive(False)
        self.missing_cbox.set_sensitive(False)
        self.failed_cbox.set_sensitive(False)
        self.__thread_finished = False
        
        self.button_close.set_sensitive(False)
        self.button_run.set_sensitive(False)
        
        r,w = os.pipe()
        utility.pipe_nowait(r)
        self.__piper = os.fdopen(r,'r')
        self.__pipew = os.fdopen(w,'w')
        
        self.__thread = threading.Thread(target=self._thread_func)
        self.__thread.daemon=True
        self.__thread.run()
        GLib.timeout_add(50,self._on_timeout)
        
    def _on_timeout(self):
        text = self.__piper.read()
        lines = text.split('\n')
        if lines:
            buffer = self.progressview.get_buffer()
            for i in lines:
                if i.startswith('[ERROR]'):
                    text = i[len('[ERROR]'):] + '\n'
                    buffer.insert_with_tags(buffer.get_end_iter(),text,self.stderr_tag)
                else:
                    if i.endswith('... '):
                        text = i
                    else:
                        text = i + '\n'
                    buffer.insert_with_tags(buffer.get_end_iter(),text,self.stdout_tag)
                    
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
                
            iter = buffer.get_iter_at_line(buffer.get_line_count())
            self.progressview.scroll_to(iter)
            
        if not self.__thread_finished:
            return True
            
        self.__pipew.close()
        return False
    # _on_timeout()
        
    def _on_thread_finished(self):
        self.__thread_finished = True
        self.button_close.set_sensitive(True)
        self.button_close.set_sensitive(True)
        self.missing_cbox.set_sensitive(True)
        self.failed_cbox.set_sensitive(True)
        
        self.__pipew.close()        
    def _on_thread_update(self,data):
        if 'fraction' in data:
            self.progress.set_fraction(data['fraction'])
        if 'text' in data:
            self.progress.set_text('text')
        self.progress.show()
        
    def _thread_func(self):
        data = {'fraction':0.0,'text':'Preparing ... '}
        GLib.idle_add(self._on_thread_update,data)
        db = sgbackup.database.Database()
        
        count = 0
        n_steps = 1
        if not self.files:
            f = sgbackup.backup.find_latest_backup()
            if f:
                self.files.append(f)
                    
        n_steps += len(self.files)
        
        if self.files:
            for f in self.files:
                if os.path.abspath(f):
                    file = f
                else:
                    file = os.path.join(CONFIG['backup.dir'],game.savegame_name,f)
                    
                count += 1
                data = {'fraction': (count/n_steps),'text': 'Checking file: {}'.format(os.path.basename(f))}
                
                if not os.path.isfile(f):
                    #print('File "{}" not found! SKIPPING'.format(file),file=self.stderr_w)
                    continue
                    
                GLib.idle_add(self._on_thread_update,data)
                backup = db.get_game_backup(self.game,os.path.basename(file))
                if not backup:
                    missing_action = self.missing_action
                    if missing_action == self.MISSING_IGNORE:
                        print('[ERROR]' + 'Checksum for file "{}" not found! SKIPPING!'.format(file),file=self.__pipew)
                        continue
                    elif self.missing_action == self.MISSING_CREATE:
                        print('[ERROR]' + 'Checksum for file "{}" not found! CREATING!'.format(file),file=self.__pipew)
                        cksum = CONFIG['backup.checksum']
                        h = hashlib.new(cksum)
                        with open(file,'rb') as ifile:
                            h.update(ifile.read())
                        hash = h.hexdigest()
                        db.add_game_backup(game,os.path.basename(file),cksum,hash)
                    elif missing_action == self.MISSING_DELETE:
                        print('[ERROR]' + 'Checksum for file "{0}" not found! DELETING FILE!'.format(file),file=self.__pipew)
                        sgbackup.backup.delete_backup(self.game,file)
                else:
                    print('[checksum:{0}] {1} ... '.format(backup['checksum'],os.path.basename(file)),end='',file=self.__pipew)
                    h = hashlib.new(backup['checksum'])
                    with open(file,'rb') as ifile:
                        h.update(ifile.read())
                    hash = h.hexdigest()
                    if backup['hash'] == hash:
                        print('OK',file=self.__pipew)
                        continue
                    else:
                        failed_action = self.failed_action
                        
                        print('FAILED',file=self.__pipew)
                        if failed_action == self.FAILED_IGNORE:
                            continue
                        elif failed_action == self.FAILED_DELETE:
                            print('[ERROR]' + 'Checksum check for file {} failed! DELETING!'.format(os.path.baesname(file)),
                                  file=self.__pipew)
                    
                
        data = {'fraction': 1.0, 'text': 'Done'}
        GLib.idle_add(self._on_thread_update,data)
        GLib.idle_add(self._on_thread_finished)
    # _thread_func()   
# CheckBackupDialog class

class CheckGamesDialog(Gtk.Dialog):
    (FAILED_IGNORE,FAILED_DELETE) = range(2)
    (MISSING_IGNORE,MISSING_CREATE,MISSING_DELETE) = range(3)
    
    def __init__(self,games=[],parent=None):
        Gtk.Dialog.__init__(self,parent)
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
    
    def get_missing_action(self):
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
        self.__thread.daemon = True
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
        missing_action = self.get_missing_action()
        failed_action = self.get_failed_action()
        
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

class VariableDialog(Gtk.Dialog):
    def __init__(self,parent=None,name='',value=''):
        def create_label(text):
            lbl = Gtk.Label(text)
            lbl.set_xalign(0.0)
            self.sizegroup.add_widget(lbl)
            return lbl
        # create_label()
        
        Gtk.Dialog.__init__(self,parent=parent)
        self.set_title('Game Variables')
        
        vbox = self.get_content_area()
        self.sizegroup = Gtk.SizeGroup()
        self.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = create_label('Name:')
        hbox.pack_start(label,False,False,5)
        self.name_entry = Gtk.Entry()
        self.name_entry.set_text(name)
        self.name_entry.connect('changed',self._on_name_entry_changed)
        hbox.pack_start(self.name_entry,True,True,0)
        vbox.pack_start(hbox,False,False,0)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = create_label('Value')
        hbox.pack_start(label,False,False,5)
        self.value_entry = Gtk.Entry()
        self.value_entry.set_text(value)
        hbox.pack_start(self.value_entry,True,True,0)
        vbox.pack_start(hbox,False,False,0)
        
        self.apply_button = self.add_button('Apply', Gtk.ResponseType.APPLY)
        if not self.name:
            self.apply_button.set_sensitive(False)
            
        self.cancel_button = self.add_button('Cancel',Gtk.ResponseType.CANCEL)
        
        self.show_all()
        
    @property
    def name(self):
        return self.name_entry.get_text()
    @name.setter
    def name(self,s):
        self.name_entry.set_text(s)
        self.name_entry.show()
        
    @property
    def value(self):
        return self.value_entry.get_text()
    @value.setter
    def value(self,s):
        self.value_entry.set_text(s)
        self.value_entry.show()
        
    def _on_name_entry_changed(self,entry):
        if self.name:
            self.apply_button.set_sensitive(True)
        else:
            self.apply_button.set_sensitive(False)
# VariableDialog class

class GameDialog(Gtk.Dialog):
    (COL_NAME,COL_VALUE) = range(2)
    
    def __init__(self,parent=None,game=None,game_id=None):
        def create_label(text,sizegroup):
            lbl = Gtk.Label(text)
            lbl.set_xalign(0.0)
            sizegroup.add_widget(lbl)
            return lbl
            
        Gtk.Dialog.__init__(self,parent=parent)
        
        self.__final_backup = False
        
        self.set_default_size(500,500)
        vbox = self.get_content_area()
        self.sizegroup = Gtk.SizeGroup()
        self.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = create_label('Database ID:',self.sizegroup)
        hbox.pack_start(label,False,False,5)
        self.dbid_label = Gtk.Label('0')
        hbox.pack_start(self.dbid_label,True,True,0) 
        vbox.pack_start(hbox,False,False,0)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = create_label('GameID:',self.sizegroup)
        hbox.pack_start(label,False,False,5)
        self.gameid_entry = Gtk.Entry()
        hbox.pack_start(self.gameid_entry,True,True,0)
        vbox.pack_start(hbox,False,False,0)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = create_label('Game Name:',self.sizegroup)

        hbox.pack_start(label,False,False,5)
        self.name_entry = Gtk.Entry()
        hbox.pack_start(self.name_entry,True,True,0)
        vbox.pack_start(hbox,False,False,0)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = create_label('Savegame Name:',self.sizegroup)
        hbox.pack_start(label,False,False,5)
        self.savegame_name_entry = Gtk.Entry()
        hbox.pack_start(self.savegame_name_entry,True,True,0)
        vbox.pack_start(hbox,False,False,0)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = create_label('Savegame Root:',self.sizegroup)
        hbox.pack_start(label,False,False,5)
        self.savegame_root_entry = Gtk.Entry()
        hbox.pack_start(self.savegame_root_entry,True,True,0)
        button = Gtk.Button.new_from_icon_name('document-open',Gtk.IconSize.BUTTON)
        button.connect('clicked',self._on_savegame_root_button_clicked)
        hbox.pack_start(button,False,False,0)
        vbox.pack_start(hbox,False,False,0)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = create_label('Savegame Directory:',self.sizegroup)
        hbox.pack_start(label,False,False,5)
        self.savegame_dir_entry = Gtk.Entry()
        hbox.pack_start(self.savegame_dir_entry,True,True,0)
        button = Gtk.Button.new_from_icon_name('document-open',Gtk.IconSize.BUTTON)
        button.connect('clicked',self._on_savegame_dir_button_clicked)
        hbox.pack_start(button,False,False,0)
        vbox.pack_start(hbox,False,False,0)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.steam_appid_label = create_label('Steam AppID:',self.sizegroup)
        self.steam_appid_label.set_sensitive(False)
        hbox.pack_start(self.steam_appid_label,False,False,5)
        self.steam_appid_entry = Gtk.Entry()
        self.steam_appid_entry.set_sensitive(False)
        hbox.pack_start(self.steam_appid_entry,True,True,0)
        self.steam_appid_switch = Gtk.Switch()
        self.steam_appid_switch.connect('notify::active',self._on_steam_appid_switch_notify_active)
        self.steam_appid_switch.set_active(False)
        hbox.pack_start(self.steam_appid_switch,False,False,0)
        vbox.pack_start(hbox,False,False,0)
        
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,0)
        
        # Variables
        self.variables_toolbar = Gtk.Toolbar()
        self.variables_toolbar.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)
        self.add_variable_button = Gtk.ToolButton()
        self.add_variable_button.set_icon_name('list-add')
        self.add_variable_button.set_label('Add Variable')
        self.add_variable_button.connect('clicked',self._on_add_variable_clicked)
        self.variables_toolbar.insert(self.add_variable_button,-1)
        
        self.edit_variable_button = Gtk.ToolButton()
        self.edit_variable_button.set_icon_name('document-edit-symbolic')
        self.edit_variable_button.set_label('Edit Variable')
        self.edit_variable_button.connect('clicked',self._on_edit_variable_clicked)
        self.variables_toolbar.insert(self.edit_variable_button,-1)
        
        self.remove_variable_button = Gtk.ToolButton()
        self.remove_variable_button.set_icon_name('list-remove')
        self.remove_variable_button.set_label('Remove Variable')
        self.remove_variable_button.connect('clicked',self._on_remove_variable_clicked)
        self.variables_toolbar.insert(self.remove_variable_button,-1)
        
        vbox.pack_start(self.variables_toolbar,False,False,0)
        
        scrolled = Gtk.ScrolledWindow()
        model = Gtk.ListStore(str,str)
        self.variables_view = Gtk.TreeView(model)
        self.variables_view.get_selection().connect('changed',self._on_varaibles_view_selection_changed)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(cell_renderer=renderer,text=self.COL_NAME)
        column.set_sort_column_id(self.COL_NAME)
        self.variables_view.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(cell_renderer=renderer,text=self.COL_VALUE)
        self.variables_view.append_column(column)
        scrolled.add(self.variables_view)
        self._on_varaibles_view_selection_changed(self.variables_view.get_selection())
        
        vbox.pack_start(scrolled,True,True,0)
            
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,0)
        
        if game:
            self._set_game_data(game,game_id)
        
        self.add_button('Apply',Gtk.ResponseType.APPLY)
        self.add_button('Cancel',Gtk.ResponseType.CANCEL)
        self.show_all()
    # __init__()
    
    @property
    def game_id(self):
        return self.gameid_entry.get_text()
    @game_id.setter
    def game_id(self,s):
        self.gameid_entry.set_text(s)
        self.gameid_entry.show()
        
    @property
    def name(self):
        return self.name_entry.get_text()   
    @name.setter
    def name(self,s):
        self.name_entry.set_text(s)
        self.name_entry.show()
        
    @property
    def savegame_name(self):
        return self.savegame_name_entry.get_text()
    @savegame_name.setter
    def savegame_name(self,s):
        if s:
            self.savegame_name_entry.set_text(s)
        else:
            self.savegame_name_entry.set_text('')
        self.savegame_name_entry.show()
        
    @property
    def savegame_root(self):
        t = string.Template(self.savegame_root_entry.get_text())
        return t.safe_substitute(self.variables)
        
    @savegame_root.setter
    def savegame_root(self,s):
        self.savegame_root_entry.set_text(s)
        self.savegame_root_entry.show()
    @property
    def raw_savegame_root(self):
        return self.savegame_root_entry.get_text()
        
    @property
    def savegame_dir(self):
        t = string.Template(self.savegame_dir_entry.get_text())
        return t.safe_substitute(self.variables)
    @savegame_dir.setter
    def savegame_dir(self,s):
        self.savegame_dir_entry.set_text(s)
    @property
    def raw_savegame_dir(self):
        return self.savegame_dir_entry.get_text()
    
    @property
    def variables(self):
        ret = sgbackup.config.get_template_vars()
        
        for row in self.variables_view.get_model():
            ret[row[self.COL_NAME]] = row[self.COL_VALUE]
            
        return ret
    @property
    def raw_variables(self):
        ret = {}
        for row in self.variables_view.get_model():
            ret[row[self.COL_NAME]] = row[self.COL_VALUE]
        return ret        
        
    @property
    def steam_appid_enabled(self):
        return self.steam_appid_switch.get_active()
    @steam_appid_enabled.setter
    def steam_appid_enabled(self,b):
        self.steam_appid_switch.set_active(bool(b))
        
    @property
    def steam_appid(self):
        if not self.steam_appid_enabled:
            return None

        s = self.steam_appid_entry.get_text()
        if not s:
            return None
        return s
    @steam_appid.setter
    def steam_appid(self,s):
        if s:
            self.steam_appid_enabled = True
            self.steam_appid_entry.set_text(s)
        else:
            self.steam_appid_enabled = False
            self.steam_appid_entry.set_text('')
   
    @property            
    def game(self):
        return sgbackup.games.Game(self.game_id,
                                   self.name,
                                   self.savegame_name,
                                   self.raw_savegame_root,
                                   self.raw_savegame_dir,
                                   id = int(self.dbid_label.get_text()),
                                   final_backup = self.__final_backup,
                                   steam_appid = self.steam_appid,
                                   variables = self.raw_variables)

    def _set_game_data(self,game,game_id):
        if isinstance(game,sgbackup.games.Game):
            self.dbid_label.set_text(str(game.id))
            self.game_id = game.game_id
            self.name = game.name
            self.savegame_name = game.savegame_name
            self.savegame_root = game.raw_savegame_root
            self.savegame_dir = game.raw_savegame_dir
            self.__final_backup = game.final_backup
            
            if game.steam_appid:
                self.steam_appid = game.steam_appid
            
            model = self.variables_view.get_model()
            for k,v in game.raw_variables.items():
                model.append((k,v))
                
            
        elif isinstance(game,configparser.ConfigParser):
            sect='game'
            if game_id:
                self.game_id = game_id
            if game.has_section(sect):
                if game.has_option(sect,'name'):
                    self.name = game.get(sect,'name')
                if game.has_option(sect,'savegame-name'):
                    self.savegame_name = game.get(sect,'savegame-name')
                if game.has_option(sect,'savegame-root'):
                    self.savegame_root = game.get(sect,'savegame-root')
                if game.has_option(sect,'savegame-dir'):
                    self.savegame_dir = game.get(sect,'savegame-dir')
                if game.has_option(sect,'final-backup'):
                    self.__final_backup = game.getboolean(sect,'final-backup')
                    
            sect = 'steam'
            if game.has_section(sect):
                if game.has_option(sect,'appid'):
                    self.steam_appid = game.get(sect,'appid')
                    
            sect = 'game-variables'
            if game.has_section(sect):
                model = self.variables_view.get_model()
                for k in game.options(sect):
                    model.append((k,game.get(k)))                
            
        elif isinstance(game,dict):
            if 'id' in game:
                self.dbid_label.set_text(str(game['id']))
            if 'game-id' in game:
                self.game_id = game['game-id']
            elif game_id:
                self.game_id = game_id
            if 'name' in game:
                self.name = game['name']
            if 'savegame-name' in game:
                self.savegame_name = game['savegame-name']
            if 'savegame-root' in game:
                self.savegame_root = game['savegame-root']
            if 'savegame-dir' in game:
                self.savegame_dir = game['savegame-dir']
            if 'final-backup' in game:
                self.__final_backup = game['final-backup']
            if 'steam-appid' in game:
                self.steam_appid = game['steam_appid']
            if 'game-variables' in game:
                model = self.variables_view.get_model()
                for k,v in dict['game-variables'].items():
                    model.append((k,v))  
        else:
            raise TypeError('Unknown "game"-type!')
    # _set_game_data()
        
    def _on_steam_appid_switch_notify_active(self,switch,state):
        if switch.get_active():
            self.steam_appid_label.set_sensitive(True)
            self.steam_appid_entry.set_sensitive(True)
        else:
            self.steam_appid_label.set_sensitive(False)
            self.steam_appid_entry.set_sensitive(False)
            
    def _on_add_variable_clicked(self,button):
        dialog = VariableDialog(parent=self)
        result = dialog.run()
        dialog.hide()
        
        if result == Gtk.ResponseType.APPLY:
            if dialog.name:
                model = self.variables_view.get_model()
                model.append([dialog.name,dialog.value])
                self.variables_view.show()
        dialog.destroy()
        
    def _on_edit_variable_clicked(self,button):
        model,iter = self.variables_view.get_selection().get_selected()
        if iter:
            v_name,v_value = model.get(iter,self.COL_NAME,self.COL_VALUE)
            dialog = VariableDialog(parent=self,name=v_name,value=v_value)
            result = dialog.run()
            dialog.hide()
            if result == Gtk.ResponseType.APPLY:
                model.set(iter,(self.COL_NAME,self.COL_VALUE),(dialog.name,dialog.value))
                self.variables_view.show()
            dialog.destroy()
        
    def _on_remove_variable_clicked(self,button):
        model,iter = self.variables_view.get_selection().get_selected()
        if iter:
            model.remove(iter)
        
    def _on_varaibles_view_selection_changed(self,selection):
        model,iter = selection.get_selected()
        if iter:
            self.edit_variable_button.set_sensitive(True)
            self.remove_variable_button.set_sensitive(True)
        else:
            self.edit_variable_button.set_sensitive(False)
            self.remove_variable_button.set_sensitive(False)
    
    def _on_savegame_root_button_clicked(self,button):
        dialog = Gtk.FileChooserDialog("Select Savegame Root-Directory",
                                       self,
                                       Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_button('Accept', Gtk.ResponseType.ACCEPT)
        dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
        if self.savegame_root:
            t = string.Template(self.savegame_root)
            path = t.substitute(sgbackup.config.get_template_vars())
            dialog.set_current_folder(path)
            
        else:
            dialog.set_current_folder(GLib.get_home_dir())
        
        result = dialog.run()
        dialog.hide()
        if result == Gtk.ResponseType.ACCEPT:
            self.savegame_root_entry.set_text(dialog.get_filename())
        dialog.destroy()
        
    def _on_savegame_dir_button_clicked(self,button):
        if not self.savegame_root:
            return
            
        def on_dialog_file_selection_changed(dialog):
            fn = dialog.get_filename()
            if os.path.normpath(fn).startswith(os.path.normpath(os.path.join(self.savegame_root,''))):
                dialog.accept_button.set_sensitive(True)
            else:
                dialog.accept_button.set_sensitive(False)
        # on_dialog_file_selection_changed()
            
        dialog = Gtk.FileChooserDialog('Select SaveGame Directory',
                                       self,
                                       Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.accept_button = dialog.add_button('Accept',Gtk.ResponseType.ACCEPT)
        dialog.cancel_button = dialog.add_button('Cancel',Gtk.ResponseType.CANCEL)
        dialog.set_create_folders(False)
        dialog.connect('selection-changed',on_dialog_file_selection_changed)
        if self.savegame_dir:
            if os.path.isabs(self.savegame_dir):
                dialog.set_current_folder(self.savegame_dir)
            else:
                dialog.set_current_folder(os.path.join(self.savegame_root,self.savegame_dir))
        else:
            dialog.set_current_folder(self.savegame_root)
            
        result = dialog.run()
        dialog.hide()
        if result == Gtk.ResponseType.ACCEPT:
            prefix = os.path.join(os.path.normpath(self.savegame_root),'')
            fn = os.path.normpath(dialog.get_filename())
            if fn.startswith(prefix):
                self.savegame_dir = fn[len(prefix):]
            else:
                self.savegame_dir = fn
        dialog.destroy()
        
    def write_game_config(self,cparser):
        section = 'game'
        if not cparser.has_section(section):
            cparser.add_section(section)
        cparser.set(section,'name',self.name)
        cparser.set(section,'savegame-name',self.savegame_name)
        cparser.set(section,'savegame-root',self.raw_savegame_root)
        cparser.set(section,'savegame-dir',self.raw_savegame_dir)
        
        if self.steam_appid_enabled and self.steam_appid:
            section = 'steam'
            if not cparser.has_section(section):
                cparser.add_section(section)
            cparser.set(section,'appid',self.steam_appid)
            
        var_model = self.variables_view.get_model()
        if len(var_model) > 0:
            section = 'game-variables'
            if not cparser.has_section(section):
                cparser.add_section(section)
            for row in var_model:
                cparser.set(section,row[self.COL_NAME],row[self.COL_VALUE])        
# GameDialog class

class RenameBackupsDialog(Gtk.MessageDialog):
    def __init__(self,old_game,new_game,parent=None):
        Gtk.MessageDialog.__init__(self,parent,
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   Gtk.ButtonsType.NONE,
                                   'Renaming SaveGame-Backups from "{0}" to "{1}".'.format(old_game.savegame_name,new_game.savegame_name))
                              
        self.__old_game = old_game
        self.__new_game = new_game
             
        self.close_button = self.add_button('Close',Gtk.ResponseType.CLOSE)
        self.close_button.set_sensitive(False)
        
        vbox = self.get_content_area()
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
        
        self.progress = Gtk.ProgressBar()
        self.progress.set_text('Renaming Files ...')
        self.vbox.pack_start(self.progress,False,False,0)
        
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
        
        self.show_all()

    @property
    def old_game(self):
        return self.__old_game
    @property
    def new_game(self):
        return self.__new_game
    
    def _on_thread_update(self,data):
        self.progress.set_text(data['text'])
        self.progress.set_fraction(data['fraction'])
        self.progress.show()
        
    def _on_thread_finished(self):
        self.progress.set_text('DONE')
        self.progress.set_fraction(1.0)
        self.progress.show()
        self.close_button.set_sensitive(True)
        
    def _thread_func(self):
        old_dir = os.path.join(CONFIG['backup.dir'],self.old_game.savegame_name)
        if not os.path.isdir(old_dir):
            GLib.idle_add(self._on_thread_finished)
            return
            
        db = sgbackup.database.Database()
        backups = sgbackup.backup.find_backups()
        
        
        n_steps = len(backups+2)
        count=0
        
        for old_fn in backups:
            count += 1
            new_fn = os.path.join(os.path.dirname(old_fn),
                                  os.path.basename(old_fn).replace(self.old_game.savegame_name,self.new_game.savegame_name))
            idle_data={
                'text': 'Renaming File: {0} -> {1}'.format(os.path.basename(old_fn),os.path.basename(new_fn)),
                'fraction': (count/n_steps)
            }
            GLib.idle_add(self._on_thread_update,idle_data)
            os.rename(old_fn,new_fn)
            sql = "UPDATE filelist SET filename=? WHERE filename=?;"
            try:
                db._db.execute(sql,(os.path.basename(new_fn),os.path.basename(old_fn)))
                db._db.commit()
            except Exception as error:
                print('Unable to change filename in database! ({0})'.format(error))
        count += 1
        new_dir=os.path.join(CONFIG['backup.dir'],new_game.savegame_name)
        idle_data = {
            'text': 'Renaming Directory: {0} -> {1}'.format(old_dir,new_dir),
            'fraction': (count/n_steps)
        }
        GLib.idle_add(self._on_thread_update,idle_data)
        try:
            os.rename(old_dir,new_dir)
        except Exception as error:
            print("Unable to rename backup dir! ({})".format(error),file=sys.stderr)
        
        GLib.idle_add(self._on_thread_finished)
    # _thread_func()
    
    def run(self):
        self.present()
        thread = threading.Thread(target=self._thread_func,dameon=True)
        thread.start()
        return Gtk.MessageDialog.run(self)
# RenameBackupsDialog class

class UpdateDatabaseDialog(Gtk.Dialog):
    def __init__(self,parent=None):
        Gtk.Dialog.__init__(self,parent=parent)
        
        self.set_default_size(600,400)
        
        self.__thread_finished = False
        self.__stderr_fd,self.__thread_stderr_fd = os.pipe()
        utility.pipe_nowait(self.__stderr_fd)
        self.__thread_stderr = os.fdopen(self.__thread_stderr_fd,'ab')
        
        self.__stdout_fd,self.__thread_stdout_fd = os.pipe()
        utility.pipe_nowait(self.__stdout_fd)
        self.__thread_stdout = os.fdopen(self.__thread_stdout_fd,'ab')
        
        self.close_button=self.add_button('Close',Gtk.ResponseType.CLOSE)
        
        vbox = self.get_content_area()
        label = Gtk.Label()
        label.set_markup('<span size="x-large">' + 'Updating Database' + '</span>')
        vbox.pack_start(label,False,False,0)
        
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
        
        self.progress = Gtk.ProgressBar()
        self.progress.set_pulse_step(0.025)
        self.progress.set_show_text(True)
        self.progress.set_text('Updating ...')
        vbox.pack_start(self.progress,False,False,0)
        
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
        
        buf = Gtk.TextBuffer()
        self.stdout_tag = buf.create_tag('stdout',foreground='green')
        self.stderr_tag = buf.create_tag('stderr',foreground='red')

        
        self.progressview_scrolled = Gtk.ScrolledWindow()
        self.progressview = Gtk.TextView()
        self.progressview.set_buffer(buf)
        self.progressview.set_editable(False)

        self.progressview_scrolled.add(self.progressview)
        vbox.pack_start(self.progressview_scrolled,True,True,0)
        
        vbox.pack_end(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
        
        self.show_all()                         
        
    def __del__(self):
        self.__thread_stderr.close()
        self.__thread_stdout.close()
        os.close(self.__stderr_fd)
        os.close(self.__stdout_fd)
        
    def _on_timeout(self):
        buf = self.progressview.get_buffer()
        encoding = sys.getdefaultencoding()
        try:
            if self.__sterr_fd:
                err_str = os.read(self.__stderr_fd,4096).decode(encoding)
                if (err_str):
                    buf.insert_with_tags(buf.get_end_iter(),err_str,self.stderr_tag)            
        except Exception:
            pass
            
        try:
            if self.__stdout_fd:
                out_str = os.read(self.__stdout_fd,4096).decode(encoding)
                if (out_str):
                    buf.insert_with_tags(buf.get_end_iter(),out_str,self.stdout_tag)
        except Exception:
            pass
            
        self.progressview.show()
        self.progressview_scrolled.set_placement(Gtk.CornerType.BOTTOM_LEFT)
        self.progressview_scrolled.show()
        
        if self.__thread_finished:
            return False
           
        self.progress.pulse()
        return True
        
    def _spawn_finish_cb(self,pid,status,data):
        self.__thread_finished = True
        self.progress.set_fraction(1.0)
        self.progress.set_text('Done')
        self.close_button.set_sensitive(True)
        GLib.spawn_close_pid(pid)
    
    def run(self):
        GLib.timeout_add(25,self._on_timeout)
        command = [sys.executable,'-m','sgbackup','database','update','--verbose',None]
        (
            spawn_ok,
            pid,
            stdin_fd,
            self.__stdout_fd,
            self.__stderr_fd
        ) = GLib.spawn_async_with_pipes(None,command,None,GLib.SpawnFlags.DO_NOT_REAP_CHILD)
        if spawn_ok:
            if self.__stdout_fd:
                utility.pipe_nowait(self.__stdout_fd)
            if self.__stderr_fd:
                utility.pipe_nowait(self.__stderr_fd)
            GLib.child_watch_add(GLib.PRIORITY_DEFAULT,pid,self._spawn_finish_cb,None)
        else:
            self.__thread_finished = True
            if self.__stdout_fd:
                os.close(self.__stdout_fd)
                self.__stdout_fd = 0
            if self.__stderr_fd:
                os.close(self.__stderr_fd)
                self.__stderr_fd = 0
            buf = self.progressview.get_buffer()
            buf.insert_with_tags(buf.get_end_iter(),"Unable to start process!",self.stderr_tag)
            
        return Gtk.Dialog.run(self)
# UpdateDatabaseDialog()

class RestoreGamesDialog(Gtk.Dialog):
    def __init__(self,parent=None,games=[]):
        Gtk.Dialog.__init__(self,parent)
        db = sgbackup.database.Database()
        self.__games = []
        self.__cancel = False
        
        if games:
            for g in games:
                found=False
                for i in self.__games:
                    if g.game_id == i.game_id:
                        found = True
                        break
                if not found:
                    self.__games.append(g)
        else:
            for gid in db.list_game_ids():
                g = db.get_game(gid)
                self.__games.append(g)
                
        vbox = self.get_content_area()
        label = Gtk.Label()
        label.set_markup('<span size="x-large" weight="bold">' 
                         + 'Restoring selected SaveGame-Backups'
                         + '</span>')
        vbox.pack_start(label,False,False,0)
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
        
        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        vbox.pack_start(self.progress,False,False,0)
        
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
        
        buttonbox = self.get_action_area()
        self.button_cancel = Gtk.Button('Cancel')
        self.button_cancel.connect('clicked',self._on_button_cancel_clicked)
        self.button_cancel.set_sensitive(False)
        buttonbox.pack_start(self.button_cancel,False,False,0)
        buttonbox.set_child_secondary(self.button_cancel,True)
        
        self.button_close = self.add_button('Close',Gtk.ResponseType.CLOSE)
        
        self.show_all()
    # __init__()
        
    @property
    def games(self):
        return self.__games
        
    def _on_button_cancel_clicked(self,button):
        self.__cancel = True
        self.button_cancel.set_sensitive(False)
        
    def _on_thread_update(self,data):
        if 'text' in data:
            self.progress.set_text(data['text'])
        if 'fraction' in data:
            self.progress.set_fraction(data['fraction'])
        self.progress.show()
        
    def _on_thread_finished(self):
        if self.__cancel:
            self.progress.set_text('Restoring backups canceled')
        else:
            self.progress.set_text('Done')
            self.progress.set_fraction(1.0)
            
        self.button_close.set_sensitive(True)
        self.button_cancel.set_sensitive(False)
        
        
    def _thread_func(self):
        def find_latest_good_savegame(db,game):
            backup = sgbackup.backup.find_latest_backup(game)
            if sgbackup.backup.check_backup(db,game,backup):
                return backup
            
            backup = None
            backup_list = []
            for i in backups.find_backups(game):
                st = os.stat(i)
                inserted = False
                for j in range(len(backup_list)):
                    f,ctime = backup_list[j]
                    if ctime > st.st_ctime:
                        backup_list.insert(j,(i,st.st_ctime))
                        inserted = True
                        break
                if not inserted:
                    backup_list.append((i,st.st_ctime))
                    
            
            for f,ctime in backup_list:
                if sgbackup.check_backup(db,game,f):
                    backup = f
                    break
                    
            return backup
        # find_latest_good_savegame
        
        db = sgbackup.database.Database()
        backup_files = []
        
        for game in self.games:
            backup = sgbackup.backup.find_latest_backup(game)
            if backup:
                backup_files.append((game,backup))
                
        n_steps = len(backup_files) + 1
        count = 1
        for game,backup in backup_files:
            if self.__cancel:
                GLib.idle_add(self._on_thread_finished)
                return
                
            data = {'fraction': (count/n_steps), 'text': 'Restoring: {} ...'.format(game.name)}
            GLib.idle_add(self._on_thread_update,data)
            sgbackup.backup.restore(db,game,backup)
            count += 1
            
        GLib.idle_add(self._on_thread_finished)            
        
    def run(self):
        thread = threading.Thread(target=self._thread_func)
        thread.daemon = True
        thread.start()
        self.button_cancel.set_sensitive(True)
        self.button_close.set_sensitive(False)
        return Gtk.Dialog.run(self)
# RestoreGamesDialog class

class RestoreBackupDialog(Gtk.Dialog):
    def __init__(self,game,parent=None,backup=None):
        Gtk.Dialog.__init__(self,parent)
        self.set_title('PySGBackup: Restore Backup')
        
        self.game = game
        self.backup = backup
        
        vbox = self.get_content_area()
        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        vbox.pack_start(self.progress,False,False,0)
        
        self.close_button = self.add_button('Close', Gtk.ResponseType.CLOSE)
        self.close_button.set_sensitive(False)
        
        self.show_all()
        
    @property
    def game(self):
        return self.__game   
    @game.setter
    def game(self,g):
        if not isinstance(g,sgbackup.games.Game):
            raise TypeError('game')
        if hasattr(self,'__game') and (self.game.game_id != g.game_id):
            self.backup = sgbackup.backup.find_latest_backup(g)
        self.__game = g
        
    @property
    def backup(self):
        if not self.__backup:
            db = sgbackup.database.Database()
            backup = sgbackup.backup.find_latest_backup(self.game)
            return backup
            
        if os.path.isabs(self.__backup):
            return self.__backup
        return os.path.join(CONFIG['backup.dir'],self.game.savegame_name,self.__backup)
        
    @backup.setter
    def backup(self,filename):
        self.__backup = filename
    
    def _on_thread_update(self,data):
        if 'text' in data:
            self.progress.set_text(data['text'])
        if 'fraction' in data:
            self.progress.set_fraction(data['fraction'])
        self.progress.show()
        
    def _on_thread_finished(self):
        self.close_button.set_sensitive(True)
        
    def _on_check_failed(self):
        #TODO
        pass
        
    def _thread_func(self):
        db = sgbackup.database.Database()
        
        data = {'text': 'Checking backup ...','fraction':0.0}
        GLib.idle_add(self._on_thread_update,data)
        
        if not sgbackup.backup.check_backup(db,self.game,self.backup):
            dialog = Gtk.MessageDialog(self,
                                       Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                       Gtk.MessageType.ERROR,
                                       Gtk.ButtonsType.CLOSE,
                                       'Checksum test on file "{0}" failed!'.format(self.backup))
            dialog.set_title('PySGBackup: Error checksum-test')
            dialog.show_all()
            dialog.run()
            dialog.hide()
            dialog.destroy()
            
            GLib.idle_add(self._on_check_failed)
            GLib.idle_add(self._on_thread_finished)
            return
            
        data = {'text':'Restoring backup ...','fraction':0.5}
        GLib.idle_add(self._on_thread_update,data)
        
        sgbackup.backup.restore(db,self.game,self.backup)
        
        data = {'text':'Done','fraction':1.0}
        GLib.idle_add(self._on_thread_update,data)
        GLib.idle_add(self._on_thread_finished)
        
    def run(self):
        thread = threading.Thread(target=self._thread_func)
        thread.daemon = True
        thread.start()
        return Gtk.Dialog.run(self)
# RestoreBackupDialog()
