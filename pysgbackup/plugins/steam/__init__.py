#-*- coding:utf-8 -*-
################################################################################
# pysgbackup.plugins.steam
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

import os
import pysgbackup
from pysgbackup.plugins import Plugin,Settings,PLUGINS
import sgbackup
from sgbackup.plugins import steam
from gi.repository import Gtk,Gio,GLib

PLUGIN_ID = 'steam'

class SteamLibraryDialog(Gtk.Dialog):
    def __init__(self,parent=None,library=None):
        Gtk.Dialog.__init__(self,parent=parent)
        
        vbox = self.get_content_area()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = Gtk.Label('Library Path:')
        hbox.pack_start(label,False,False,5)
        self.lib_entry = Gtk.Entry()
        if library:
            self.lib_entry.set_text(library)
        hbox.pack_start(self.lib_entry,True,True,5)
        self.lib_button = Gtk.Button.new_from_icon_name('document-open',Gtk.IconSize.BUTTON)
        self.lib_button.connect('clicked',self._on_lib_button_clicked)
        hbox.pack_start(self.lib_button,False,False,5)
        
        vbox.pack_start(hbox,False,False,0)
        
        self.add_button('Apply',Gtk.ResponseType.APPLY)
        self.add_button('Cancel',Gtk.ResponseType.CANCEL)
        
        self.show_all()
    # SteamLibraryDialog.__init__()
    
    def _on_lib_button_clicked(self,button):
        dialog = Gtk.FileChooserDialog('Select Steam Library',self,Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_button('Accept',Gtk.ResponseType.ACCEPT)
        dialog.add_button('Cancel',Gtk.ResponseType.CANCEL)
        dialog.set_create_folders(False)
        if self.lib_entry.get_text():
            dialog.set_current_folder(self.lib_entry.get_text())
            
        result = dialog.run()
        dialog.hide()
        if result == Gtk.ResponseType.ACCEPT:
            self.lib_entry.set_text(dialog.get_filename())
            
        dialog.destroy()
    # SteamLibraryDialog._on_lib_button_clicked()
        
    def get_lib_dir(self):
        return self.lib_entry.get_text()
# SteamLibraryDialog class

class GameFoundDialog(Gtk.MessageDialog):
    (RESPONSE_ADD,RESPONSE_IGNORE,RESPONSE_SKIP,RESPONSE_CANCEL) = (1,2,3,Gtk.ResponseType.CANCEL)
    def __init__(self,parent,name):
        Gtk.MessageDialog.__init__(self,
                                   parent,
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   Gtk.MessageType.QUESTION,
                                   Gtk.ButtonsType.NONE,
                                   'New Steam-Game "{0}" found!\nHow do you want to proceed?'.format(name))
        
        self.add_button('Add',self.RESPONSE_ADD)
        self.add_button('Ignore',self.RESPONSE_IGNORE)
        self.add_button('Skip',self.RESPONSE_SKIP)
        self.add_button('Cancel',self.RESPONSE_CANCEL)
# GameFoundDialog class
    

class SteamSettings(Settings):
    COL_LIBRARY = 0
    def __init__(self):
        Settings.__init__(self,PLUGIN_ID,'Steam Settings',
                          attribute='steam_settings')
        
    def _on_enable_switch_toggled(self,switch,status,widget):
        if switch.get_active():
            PLUGINS[PLUGIN_ID].enable(pysgbackup.application.appwindow)
            widget.libview_frame.set_sensitive(True)
        else:
            PLUGINS[PLUGIN_ID].disable(pysgbackup.application.appwindow)
            widget.libview_frame.set_sensitive(False)
    # SteamSettings._on_enable_switch_toggled()
    
    def do_create_widget(self,dialog):
        def on_add_button_clicked(button,d,w):
            dialog = SteamLibraryDialog(d)
            result = dialog.run()
            libdir = dialog.get_lib_dir()
            if result == Gtk.ResponseType.APPLY and libdir and os.path.isdir(libdir):
                model = w.libview.get_model()
                exists = False
                for i in model:
                    if model[self.COL_LIBRARY] == libdir:
                        exists = True
                        break
                if not exists:
                    model.append([libdir])
                    w.libview.show()
            dialog.destroy()
        # on_add_button_clicked()
        
        def on_remove_button_clicked(button,d,w):
            model,iter = w.libview.get_selection().get_selected()
            if iter:
                model.remove(iter)
            w.libview.show()
        # on_remove_button_clicked()
            
        def on_edit_button_clicked(button,d,w):
            model,iter = w.libview.get_selection().get_selected()
            if iter:
                dialog = SteamLibraryDialog(d,model[iter][self.COL_LIBRARY])
                result = dialog.run()
                libdir = dialog.get_lib_dir()
                if result == Gtk.ResponseType.APPLY and libdir and os.path.isdir(libdir):
                    model.set_value(iter,self.COL_LIBRARY,libdir)
                    w.libview.show()
        # on_edit_button_clicked()
            
        w = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = Gtk.Label('Enable Steam Plugin:')
        hbox.pack_start(label,False,False,5)
        w.enable_switch = Gtk.Switch()
        hbox.pack_end(w.enable_switch,False,False,5)
        w.pack_start(hbox,False,False,0)
        
        w.libview_frame = Gtk.Frame.new('Steam Libraries')
        w.libview_frame.set_border_width(5)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        w.libview_toolbar = Gtk.Toolbar()
        w.libview_toolbar.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)
        
        image = Gtk.Image.new_from_icon_name('list-add',Gtk.IconSize.SMALL_TOOLBAR)
        w.libview_add_toolbutton = Gtk.ToolButton.new(image,'Add')
        w.libview_add_toolbutton.connect('clicked',on_add_button_clicked,dialog,w)
        w.libview_toolbar.insert(w.libview_add_toolbutton,-1)
        
        image = Gtk.Image.new_from_icon_name('document-edit-symbolic',Gtk.IconSize.SMALL_TOOLBAR)
        w.libview_edit_toolbutton = Gtk.ToolButton.new(image,'Edit')
        w.libview_edit_toolbutton.connect('clicked',on_edit_button_clicked,dialog,w)
        w.libview_toolbar.insert(w.libview_edit_toolbutton,-1)
        
        image = Gtk.Image.new_from_icon_name('list-remove',Gtk.IconSize.SMALL_TOOLBAR)
        w.libview_remove_toolbutton = Gtk.ToolButton.new(image,'Remove')
        w.libview_remove_toolbutton.connect('clicked',on_remove_button_clicked,dialog,w)
        w.libview_toolbar.insert(w.libview_remove_toolbutton,-1)
        #TODO
        vbox.pack_start(w.libview_toolbar,False,False,0)
        
        sw = Gtk.ScrolledWindow()
        model = Gtk.ListStore(str)
        for i in sgbackup.config.CONFIG['steam.libraries'].split(','):
            model.append([i])
        w.libview = Gtk.TreeView(model=model)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Steam Library',renderer,text=self.COL_LIBRARY)
        column.set_sort_column_id(self.COL_LIBRARY)
        w.libview.append_column(column)
        
        sw.add(w.libview)
        vbox.pack_start(sw,True,True,0)
        w.libview_frame.add(vbox)
        w.pack_start(w.libview_frame,True,True,0)
                
        w.enable_switch.connect('notify::active',self._on_enable_switch_toggled,w)
        w.enable_switch.set_active(sgbackup.plugins.PLUGINS['steam'].enabled)
        
        return w
    # SteamSettings.do_create_widget()
    
    def do_save(self,dialog):
        w = dialog.steam_settings
        if w.enable_switch.get_active():
            steam_libs = []
            for i in w.libview.get_model():
                steam_libs.append(i[self.COL_LIBRARY])
                
            sgbackup.CONFIG['steam.libraries'] = ','.join(steam_libs)
# SteamSettings class

class SteamPlugin(Plugin):
    UI_FILE = os.path.join(os.path.dirname(__file__),'menu.ui')
    
    def __init__(self):
        Plugin.__init__(self,PLUGIN_ID,'Steam',
                        version=sgbackup.config.version(),
                        settings=SteamSettings(),
                        sgbackup_plugin='steam',
                        sgbackup_plugin_enable=True,
                        menu={'file':self.UI_FILE,'object':'steam-menu'})
    # SteamPlugin.__init__()
            
    def on_action_steam_scan(self,action,data,appwindow):
        db = sgbackup.database.Database()
        
        entry_changed = False
        for steam_game in steam.scan_steamlibs():
            game = db.get_game_by_steam_appid(steam_game['appid'])
            if not game:
                if db.ignore_steamapp(steam_game['appid']):
                    continue
                    
                dialog = GameFoundDialog(appwindow,steam_game['name'])
                result = dialog.run()
                dialog.hide()
                if result == dialog.RESPONSE_ADD:
                    game = sgbackup.games.Game('new-game',steam_game['name'],'','','',
                                               id=0,
                                               steam_appid=steam_game['appid'],
                                               variables={
                                                   'STEAM_APPID': steam_game['appid'],
                                                   'INSTALLDIR': steam_game['installdir']
                                               })
                    game_dialog = pysgbackup.dialogs.GameDialog(appwindow,game)
                    result = game_dialog.run()
                    game_dialog.hide()
                    if result == Gtk.ResponseType.APPLY:
                        db.add_game(game_dialog.game)
                        appwindow.update_gameview()
                    elif result == Gtk.ResponseType.CANCEL:
                        continue
                    entry_changed = True
                    game_dialog.destroy()
                elif result == dialog.RESPONSE_IGNORE:
                    db.add_ignore_steamapp(steam_game['appid'])
                elif result == dialog.RESPONSE_SKIP:
                    continue
                elif result == dialog.RESPONSE_CANCEL:
                    break
            else:
                if not 'INSTALLDIR' in game.variables or steam_game['installdir'] != game.variables['INSTALLDIR']:
                    dialog = Gtk.MessageDialog(appwindow,
                                               Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                               Gtk.MessageType.QUESTION,
                                               Gtk.ButtonsType.YES_NO,
                                               'Installdir of game "{0}" changed!\nDo you want to fix it?'.format(game.name))
                    result = dialog.run()
                    dialog.hide()
                    if result == Gtk.ResponseType.YES:
                        game.variables['INSTALLDIR'] = steam_game['installdir']
                        db.add_game(game)
                    entry_changed = True
                    dialog.destroy()
        db.close()
        dialog = Gtk.MessageDialog(appwindow,
                                   Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                   Gtk.MessageType.INFO,
                                   Gtk.ButtonsType.OK,
                                   'Steam scan complete!')
        dialog.run()
        dialog.hide()
        dialog.destroy()
        if entry_changed:
            appwindow.update_gameview()
        
    # SteamPlugin.on_action_steam_scan()
        
    def do_enable(self,appwindow):
        if not hasattr(appwindow,'action_steam_scan'):
            appwindow.action_steam_scan = Gio.SimpleAction.new('steam-scan',None)
            appwindow.action_steam_scan.connect('activate',self.on_action_steam_scan,appwindow)
            appwindow.add_action(appwindow.action_steam_scan)
        else:
            appwindow.action_steam_scan.set_enabled(True)
            
        Plugin.do_enable(self,appwindow)
    # SteamPlugin.do_enable()
    
    def do_disable(self,appwindow):
        if hasattr(appwindow,'action_steam_scan'):
            appwindow.action_steam_scan.set_enabled(False)
            
        Plugin.do_disable(self,appwindow)
    # SteamPlugin.do_disable()
# SteamPlugin class

plugin = SteamPlugin()

