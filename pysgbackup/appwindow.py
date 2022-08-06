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
from gi.repository import Gtk,Gio,GLib

import sgbackup
import os

from . import settings,backupdialog

import pysgbackup

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
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(os.path.dirname(__file__),'menu.ui'))
        builder.connect_signals(self)
        
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        self.headerbar = Gtk.HeaderBar()
        self.headerbar.set_show_close_button(True)
        self.headerbar.set_decoration_layout(':minimize,maximize,close')
        self.headerbar.set_title(self.get_title())
        self.menu_button = Gtk.MenuButton()
        image = Gtk.Image.new_from_icon_name('open-menu-symbolic',Gtk.IconSize.BUTTON)
        self.menu_button.set_image(image)
        appmenu = builder.get_object('appmenu')
        self.menu_button.set_menu_model(appmenu)
        self.headerbar.pack_start(self.menu_button)
        
        self.set_titlebar(self.headerbar)
        
        
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
        renderer.set_radio(True)
        column = Gtk.TreeViewColumn('Latest',renderer,active=self.BV_COL_LATEST)
        self.backupview.append_column(column)
        
        self.backupview_scrolled.add(self.backupview)
        self.paned.pack2(self.backupview_scrolled,False,True)
        
        self.vbox.pack_start(self.paned,True,True,0)
        self.paned.set_position(300)
        
        self.statusbar = Gtk.Statusbar()
        self.vbox.pack_start(self.statusbar,False,False,0)
        
        self.add(self.vbox)
        
        self._on_gameview_selection_changed(self.gameview.get_selection())
        
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
        if len(model) > 0:
            self._action_backup_all.set_enabled(True)
        else:
            self._action_backup_all.set_enabled(False)
            
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
            
        self._action_backup = add_simple_action('backup',self._on_action_backup)
        self._action_backup_all = add_simple_action('backup-all',self._on_action_backup_all)
        
        add_simple_action('settings',self._on_action_settings)
            
    
    def _on_gameview_selection_changed(self,selection):
        self.backupview.set_model(self.__create_backupview_model())
        model,iter = selection.get_selected()
        if iter:
            self._action_backup.set_enabled(True)
        else:
            self._action_backup.set_enabled(False)
        
    def _on_action_backup(self,action,data):
        model,iter = self.gameview.get_selection().get_selected()
        if iter:
            game_id = model.get_value(iter,self.GV_COL_GAMEID)
            game=sgbackup.db.get_game(game_id)
            
            if not game:
                dialog=Gtk.MessageDialog(self,
                                         Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                         Gtk.MessageType.ERROR,
                                         Gtk.ButtonsType.CLOSE,
                                         'Unable to backup game with id "{0}!"'.format(game_id))
                dialog.connect('response', lambda d,r: d.destroy())
                dialog.format_secondary_text('Game was not found in database!')
                dialog.run()
                return
                
            dialog = backupdialog.BackupDialog(self)
            dialog.add_game(game)
            dialog.run()
            self.update_backupview()
        
    def _on_action_backup_all(self,action,data):
        game_ids = sgbackup.db.list_game_ids()
        if game_ids:
            dialog = backupdialog.BackupDialog(self)
            for gid in game_ids:
                game = sgbackup.db.get_game(gid)
                if game and not game.final_backup:
                    dialog.add_game(game)
            dialog.run()
        
        
    def _on_action_settings(self,action,data):
        dialog = settings.SettingsDialog(parent=self)
        dialog.run()
        
    def update_gameview(self):
        self.gameview.set_model(self.__create_gameview_model())
        self.gameview.show()
        
    def update_backupview(self):
        self.backupview.set_model(self.__create_backupview_model())
        self.backupview.show()
        
        
