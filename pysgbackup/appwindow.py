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
from sgbackup.config import CONFIG

import os
import configparser
import threading

from . import settings,backupdialog,dialogs

import pysgbackup

class AppWindow(Gtk.ApplicationWindow):
    (
        GV_COL_ID,
        GV_COL_GAMEID,
        GV_COL_NAME,
        GV_COL_SAVEGAME_NAME,
        GV_COL_SAVEGAME_ROOT,
        GV_COL_SAVEGAME_DIR,
        GV_COL_FINAL,
        GV_COL_STEAM_APPID
    ) = range(8)
    
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
        self.set_default_icon_name('media-floppy-symbolic')
        self.set_icon_name('media-floppy-symbolic')
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
        model = Gtk.ListStore(int,str,str,str,str,str,bool,str)
        db = sgbackup.database.Database()
        for game_id in db.list_game_ids():
            game = db.get_game(game_id)
            if game:
                model.append([game.id,
                             game.game_id,
                             game.name,
                             game.savegame_name,
                             game.savegame_root,
                             game.savegame_dir,
                             game.final_backup,
                             game.steam_appid])
        if len(model) > 0:
            self._action_backup_all.set_enabled(True)
            self._action_check_all_backups.set_enabled(True)
        else:
            self._action_backup_all.set_enabled(False)
            self._action_check_all_backups.set_enabled(False)
            
        return model
        
    def __create_backupview_model(self):
        model = Gtk.ListStore(str,str,bool)
        
        gv_model,iter = self.gameview.get_selection().get_selected()
        if iter:
            db = sgbackup.database.Database()
            game = db.get_game(gv_model.get_value(iter,self.GV_COL_GAMEID))
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
        self._action_unfinal_game = add_simple_action('unfinal-game',self._on_action_unfinal_game)
        self._action_final_backup = add_simple_action('final-backup',self._on_action_final_backup)
        self._action_check_backups = add_simple_action('check-backups',self._on_action_check_backups)
        self._action_check_all_backups = add_simple_action('check-all-backups',self._on_action_check_all_backups)
        self._action_edit_game = add_simple_action('edit-game',self._on_action_edit_game)
        self._action_delete_game = add_simple_action('delete-game',self._on_action_delete_game)
        
        add_simple_action('database-vacuum',self._on_action_database_vacuum)
        add_simple_action('refresh',self._on_action_refresh)
        add_simple_action('add-game',self._on_action_add_game)
        add_simple_action('settings',self._on_action_settings)
            
    
    def _on_gameview_selection_changed(self,selection):
        self.backupview.set_model(self.__create_backupview_model())
        model,iter = selection.get_selected()
        if iter:
            self._action_backup.set_enabled(True)
            self.headerbar.set_subtitle(model.get_value(iter,self.GV_COL_NAME))
            self._action_check_backups.set_enabled(True)
            self._action_edit_game.set_enabled(True)
            self._action_delete_game.set_enabled(True)
            if model.get_value(iter,self.GV_COL_FINAL):
                self._action_unfinal_game.set_enabled(True)
                self._action_final_backup.set_enabled(False)
            else:
                self._action_unfinal_game.set_enabled(False)
                self._action_final_backup.set_enabled(True)
        else:
            self.headerbar.set_subtitle('')
            self._action_backup.set_enabled(False)
            self._action_final_backup.set_enabled(False)
            self._action_unfinal_game.set_enabled(False)
            self._action_check_backups.set_enabled(False)
            self._action_edit_game.set_enabled(False)
            self._action_delete_game.set_enabled(False)
        
    def _on_action_backup(self,action,data):
        model,iter = self.gameview.get_selection().get_selected()
        if iter:
            db = sgbackup.database.Database()
            game_id = model.get_value(iter,self.GV_COL_GAMEID)
            game=db.get_game(game_id)
            db.close()
            
            if not game:
                dialog=Gtk.MessageDialog(self,
                                         Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                         Gtk.MessageType.ERROR,
                                         Gtk.ButtonsType.CLOSE,
                                         'Unable to backup game with id "{0}!"'.format(game_id))
                dialog.connect('response', lambda d,r: d.destroy())
                dialog.format_secondary_text('Game was not found in database!')
                dialog.run()
                dialog.destroy()
                return
                
            dialog = dialogs.BackupDialog(self)
            dialog.add_game(game)
            dialog.run()
            dialog.hide()
            dialog.destroy()
            self.update_backupview()
        
    def _on_action_refresh(self,action,data):
        self.gameview.set_model(self.__create_gameview_model())
        self.gameview.show()        

    def _on_action_database_vacuum(self,action,data):
        def on_timeout(dialog):
            if not dialog.thread_finished:
                dialog.progress.pulse()
                return True
            return False
            
        def on_thread_finished(dialog):
            dialog.thread_finished = True
            dialog.progress.set_text('DONE')
            dialog.progress.set_fraction(1.0)
            dialog.close_button.set_sensitive(True)
            
        def thread_func(dialog):
            db = sgbackup.database.Database()
            db._db.execute('VACUUM;')
            GLib.idle_add(on_thread_finished,dialog)
        
        dialog = Gtk.MessageDialog(self,
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   Gtk.MessageType.INFO,
                                   Gtk.ButtonsType.NONE,
                                   "Running VACUUM on database.")
        dialog.thread_finished = False
        vbox = dialog.get_content_area()
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,0)
        dialog.progress = Gtk.ProgressBar()
        dialog.progress.set_pulse_step(0.2)
        dialog.progress.set_text('Running VACUUM')
        vbox.pack_start(dialog.progress,False,False,0)
        vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,0)
        dialog.close_button = dialog.add_button('Close',Gtk.ResponseType.CLOSE)
        dialog.close_button.set_sensitive(False)
        dialog.show_all()
        
        thread = threading.Thread(target=thread_func,args=(dialog,),daemon=True)
        GLib.timeout_add(125,on_timeout,dialog)
        thread.start()
        
        dialog.run()
        dialog.hide()
        dialog.destroy()
        
    def _on_action_add_game(self,action,data):
        dialog = dialogs.GameDialog(self)
        result = dialog.run()
        dialog.hide()
        if result == Gtk.ResponseType.APPLY:
            db = sgbackup.database.Database()
            db.add_game(dialog.game)
            cparser = configparser.ConfigParser()
            dialog.write_game_config(cparser)
            with open(os.path.join(CONFIG['user-gameconf-dir'],'.'.join((dialog.game_id,'game'))), 'w') as ofile:
                cparser.write(ofile)
            self.gameview.set_model(self.__create_gameview_model())
            self.gameview.show()        
        dialog.destroy()        
        
        
    # _on_action_add_game()
    
    def _on_action_edit_game(self,action,data):
        model,iter = self.gameview.get_selection().get_selected()
        if iter:
            db = sgbackup.database.Database()
            gameid = model.get_value(iter,self.GV_COL_GAMEID)
            game = db.get_game(gameid)
            if not game:
                (
                    name,
                    sgname,
                    sgroot,
                    sgdir,
                    final,
                    steam_appid
                ) = model.get(iter,
                              self.GV_COL_NAME,
                              self.GV_COL_SAVEGAME_NAME,
                              self.GV_COL_SAVEGAME_ROOT,
                              self.GV_COL_SAVEGAME_DIR,
                              self.GV_COL_FINAL,
                              self.GV_COL_STEAM_APPID)
                game = {
                    'game-id': gameid,
                    'name': name,
                    'savegame-name': sgname,
                    'savegame-root': sgroot,
                    'savegame-dir': sgdir,
                    'final-backup': final,
                }
                if steam_appid:
                    game['steam-appid'] = steam_appid

            dialog = dialogs.GameDialog(parent=self,game=game)
            result = dialog.run()
            dialog.hide()
            if result == Gtk.ResponseType.APPLY:
                g = dialog.game
                db = sgbackup.database.Database()
                db.add_game(g)
                if g.game_id != model.get_value(iter,GV_COL_GAMEID):
                    gc = os.path.join(CONFIG['user-gameconf-dir'],'.'.join((gameid,'game')))
                    if os.path.isfile(gc):
                        os.unlink(gc)
                gc = os.path.join(CONFIG['user-gameconf-dir'],'.'.join((g.game_id,'game')))
                cparser = configparser.ConfigParser()
                dialog.write_game_config(cparser)
                with open(gc,'w') as ofile:
                    cparser.write(gc)                    
            dialog.destroy()
            
    # _on_action_edit_game()
    
    def _on_action_delete_game(self,action,data):
        iter,model = self.gameview.get_selection().get_selected()
        if iter:
            gameid = model.get_value(iter,self.GV_COL_GAMEID)
            gc = os.path.join(CONFIG['user-gameconf-dir'],'.'.join(gameid,'game'))
            if os.path.isfile(gc):
                dialog = Gtk.MessageDialog(self,
                                           Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                           Gtk.MessageType.QUESTION,
                                           Gtk.ButtonsType.YES_NO,
                                           'Delete GameConf for game "{}"?'.format(model.get_value(iter,GV_COL_NAME)))
                result = dialog.run()
                dialog.hide()
                if result == Gtk.ResponseType.YES:
                    os.unlink(gc)
            db = sgbackup.database.Database()
            db.delete_game(gameid)
            model.remove(iter)
            self.gameview.show()
        
    def _on_action_backup_all(self,action,data):
        db = sgbackup.database.Database()
        game_ids = db.list_game_ids()
        if game_ids:
            dialog = dialogs.BackupDialog(self)
            for gid in game_ids:
                game = db.get_game(gid)
                if game and not game.final_backup:
                    dialog.add_game(game)
            db.close()
            dialog.run()
            dialog.hide()
            dialog.destroy()
        
    def _on_action_final_backup(self,action,data):            
        model,iter = self.gameview.get_selection().get_selected()
        if iter:
            db = sgbackup.database.Database()
            game_id = model.get_value(iter,self.GV_COL_GAMEID)
            game = db.get_game(game_id)
            db.close()
            
            if game:
                dialog = Gtk.MessageDialog(self,
                                           Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                           Gtk.MessageType.QUESTION,
                                           Gtk.ButtonsType.YES_NO,
                                           'Finalize game "{0}" and create a final backup?'.format(game.name))
                dialog.format_secondary_text('Finalized games wont show up in normal backups!')
                result = dialog.run()
                dialog.destroy()
                if result == Gtk.ResponseType.YES:
                    fb_dialog = dialogs.FinalBackupDialog(game,self)
                    result = fb_dialog.run()
                    fb_dialog.destroy()
                    self.update_gameview()
                    self.gameview_select_game(game)
                
        
    def _on_action_unfinal_game(self,action,data):
        model,iter = self.gameview.get_selection().get_selected()
        if iter:
            db = sgbackup.database.Database()
            game_id = model.get_value(iter,self.GV_COL_GAMEID)
            game = db.get_game(game_id)
            db.close()
            if game:
                dialog=Gtk.MessageDialog(self,
                                         Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                         Gtk.MessageType.QUESTION,
                                         Gtk.ButtonsType.YES_NO,
                                         'Do you really want to unfinal Game "{0}"?'.format(game.name))
                dialog.format_secondary_text('Games that are not finalized show up in normal backups!')
                result = dialog.run()
                dialog.destroy()
                
                if result == Gtk.ResponseType.YES:
                    unfinal_dialog = dialogs.UnfinalGameDialog(game,self)
                    unfinal_dialog.run()
                    unfinal_dialog.destroy()
                    self.update_gameview()
                    self.gameview_select_game(game)
        
    def _on_action_check_backups(self,action,data):
        model,iter = self.gameview.get_selection().get_selected()
        if iter:
            db = sgbackup.database.Database()
            game = db.get_game(model.get_value(iter,self.GV_COL_GAMEID))
            db.close()
            if game:
                dialog = dialogs.CheckGamesDialog(games=[game],parent=self)
                dialog.run()
                dialog.destroy()                
    
    def _on_action_check_all_backups(self,action,data):
        db = sgbackup.database.Database()
        games = []
        for gid in db.list_game_ids():
            game = db.get_game(gid)
            if game:
                games.append(gid)
                
        db.close()
        
        if games:
            dialog = dialogs.CheckGamesDialog(games=games,parent=self)
            dialog.run()
            dialog.destroy()
        
    def _on_action_settings(self,action,data):
        dialog = settings.SettingsDialog(parent=self)
        result = dialog.run()
        if result == Gtk.ResponseType.APPLY:
            dialog.save_settings()
        dialog.destroy()
        
    def gameview_select_game(self,game):
        if isinstance(game,str):
            game_id = game
        elif isinstance(game,sgbackup.games.Game):
            game_id = game.game_id
        else:
            raise TypeError('game')
            
        gv_model = self.gameview.get_model()
        for i in range(len(gv_model)):
            path = Gtk.TreePath(i)
            iter = gv_model.get_iter(path)
            if gv_model.get_value(iter,self.GV_COL_GAMEID) == game_id:
                self.gameview.get_selection().select_iter(iter)
                break

    def update_gameview(self):
        self.gameview.set_model(self.__create_gameview_model())
        self.gameview.show()
        
    def update_backupview(self):
        self.backupview.set_model(self.__create_backupview_model())
        self.backupview.show()
        
        
