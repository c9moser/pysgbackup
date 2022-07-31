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
from gi.repository import Gtk

import sgbackup
import os

from . import settings

class AppWindow(Gtk.ApplicationWindow):
    (
        GV_COL_ID,
        GV_COL_GAMEID,
        GV_COL_NAME,
        GV_COL_SAVEGAME_NAME,
        GV_COL_SAVEGAME_ROOT,
        GV_COL_SAVEGAME_DIR,
        GV_COL_FINAL
    ) = range(7)
    
    (
        BV_COL_FILENAME,
        BV_COL_BASENAME,
        BV_COL_LATEST
    ) = range(3)
    
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.__create_actions()
        self.set_title('PySGBackup')
        self.set_default_size(600,600)
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(os.path.dirname(__file__),'menu.ui'))
        builder.connect.signals(self)
        menubar = builder.get_object('menubar')
        
        self.menubar = Gtk.Menubar.new_from_model(menubar)
        
        self.vbox.pack_start(self.menubar,False,False,0)
        
        self.toolbar = Gtk.Toolbar()
        self.vbox.pack_start(self.toolbar,False,False,0)
        
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        
        # gameview
        self.gameview_scrolled = Gtk.ScrolledWindow()
        self.gameview = Gtk.TreeView(self.__create_gameview_model())
        self.gameview.get_selection().connect('changed',self._on_gameview_selection_changed)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('ID',renderer,text=self.GV_COL_ID)
        column.set_sort_column_id(self.GV_COL_ID)
        self.gameview.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('GameID',renderer,text=self.GV_COL_GAMEID)
        column.set_sort_column_id(self.GV_COL_GAMEID)
        self.gameview.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Name', renderer,text=self.GV_COL_NAME)
        column.set_sort_column_id(self.GV_COL_NAME)
        self.gameview.append_column(column)
        
        renderer = Gtk.CellRendererToggle()
        renderer.set_activatable(False)
        column = Gtk.TreeViewColumn('Final',renderer,active=self.GV_COL_FINAL)
        self.gameview.append_column(column)
        
        self.gameview_scrolled.add(self.gameview)
        self.paned.pack1(self.gameview_scrolled,True,False)
        
        
        # backup view
        self.backupview_scrolled = Gtk.ScrolledWindow()
        self.backupview = Gtk.TreeView(self.__create_backupview_model())
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Savegame Backup',renderer,text=self.BV_COL_BASENAME)
        column.set_sort_column_id(self.BV_COL_BASENAME)
        self.backupview.append_column(column)
        
        renderer = Gtk.CellRendererToggle()
        renderer.set_activatable(False)
        column = Gtk.TreeViewColumn('Latest',renderer,active=self.BV_COL_LATEST)
        self.backupview.append_column(column)
        
        self.backupview_scrolled.add(self.backupview)
        self.paned.pack2(self.backupview_scrolled,False,True)
        
        self.vbox.pack_start(self.paned,True,True,0)
        self.paned.set_position(300)
        
        self.add(self.vbox)
        
        self.show_all()
        
        
    def __create_gameview_model(self):
        model = Gtk.ListStore(int,str,str,str,str,str,bool)
        
        for game_id in sgbackup.db.list_game_ids():
            game = sgbackup.db.get_game(game_id)
            if game:
                model.append([game.id,
                             game.game_id,
                             game.name,
                             game.savegame_name,
                             game.savegame_root,
                             game.savegame_dir,
                             game.final_backup])
        return model
        
    def __create_backupview_model(self):
        model = Gtk.ListStore(str,str,bool)
        
        gv_model,iter = self.gameview.get_selection().get_selected()
        if iter:
            game = sgbackup.db.get_game(gv_model.get_value(iter,self.GV_COL_GAMEID))
            if game:
                latest_backup = sgbackup.backup.find_latest_backup(game)
                
                for i in sgbackup.backup.find_backups(game):
                    model.append([i,os.path.basename(i),(latest_backup == i)])        
                
        return model
        
    def __create_actions(self):
        def add_simple_action(name,callback):
            action = Gio.SimpleAction.new(name,None)
            action.connect('activate',callback)
            self.add_action(action)
            return action
            
    
    def _on_gameview_selection_changed(self,selection):
        self.backupview.set_model(self.__create_backupview_model())
        
    def _on_action_preferences(self,action,data):
        dialog = settings.SettingDialog(parent=self)
        
        dialog.run()
