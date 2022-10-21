#-*- coding:utf-8 -*-
################################################################################
# pysgbackup.plugins.checksum
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

import sgbackup

if 'checksum' in sgbackup.plugins.PLUGINS:
    from gi.repository import Gio,Gtk
    import os
    import pysgbackup
    from pysgbackup import plugins
    import sgbackup
    from sgbackup.config import CONFIG
    from sgbackup.plugins import checksum
    from sgbackup.config import CONFIG

    PLUGIN_ID = 'checksum'
    MENU_FILE = os.path.join(os.path.dirname(__file__),'menu.ui')
    
    class ChecksumSettings(plugins.Settings):
        def __init__(self):
            plugins.Settings.__init__(self,PLUGIN_ID,'Checksum Settings',
                                      attribute='checksum_settings')
    
        def _on_enable_switch_changed(self,switch,state,dialog,widget):
            active = switch.get_active()
            engine = 'pysgbackup'
            if active:
                dialog.plugin_enable(engine,PLUGIN_ID)
                widget.algorithm_label.set_sensitive(True)
                widget.algorithm_combobox.set_sensitive(True)
                widget.bsdtags_label.set_sensitive(True)
                widget.bsdtags_switch.set_sensitive(True)
                widget.check_label.set_sensitive(True)
                widget.check_switch.set_sensitive(True)
            else:
                dialog.plugin_disable(engine,PLUGIN_ID)
                widget.algorithm_label.set_sensitive(False)
                widget.algorithm_combobox.set_sensitive(False)
                widget.bsdtags_label.set_sensitive(False)
                widget.bsdtags_switch.set_sensitive(False)
                widget.check_label.set_sensitive(False)
                widget.check_switch.set_sensitive(False)
            
        def _on_plugin_enable(self,dialog,plugin_id):
            if plugin_id == PLUGIN_ID:
                dialog.checksum_settings.enable_switch.set_active(True)
            
        def _on_plugin_disable(self,dialog,plugin_id):
            if plugin_id == PLUGIN_ID:
                dialog.checksum_settings.enable_switch.set_active(False)
        
        def do_create_widget(self,dialog):
            def create_label(text,sizegroup):
                l = Gtk.Label(text)
                l.set_xalign(0.0)
                sizegroup.add_widget(l)
                return l
            # create_label()
            
            def listbox_add_widget(listbox,widget):
                lbr = Gtk.ListBoxRow()
                lbr.add(widget)
                listbox.add(lbr)
            # listbox_add_widget()
            
            def on_plugin_enable(dialog,engine,plugin):
                if engine == 'pysgbackup' and plugin == 'checksum':
                    if not w.enable_switch.get_active():
                        w.enable_switch.set_active(True)
            # on_plugin_enable()
            
            def on_plugin_disable(dialog,engine,plugin):
                if engine == 'pysgbackup' and plugin == 'checksum':
                    if w.enable_switch.get_active():
                        w.enable_switch.set_active(False)
            # on_plugin_disable()
            
            w = Gtk.ScrolledWindow()
            w.sizegroup = Gtk.SizeGroup()
            w.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
            
            lb = Gtk.ListBox()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            label = create_label("Enable Plugin:",w.sizegroup)
            hbox.pack_start(label,False,False,5)
            w.enable_switch = Gtk.Switch()
            w.enable_switch.connect('notify::active',self._on_enable_switch_changed,dialog,w)
            hbox.pack_end(w.enable_switch,False,False,5)
            listbox_add_widget(lb,hbox)
            
            w.enable_switch.set_active(plugins.PLUGINS[PLUGIN_ID].enabled)
            
            dialog.connect('plugin-enable',on_plugin_enable)
            dialog.connect('plugin-disable',on_plugin_disable)
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            w.algorithm_label = create_label("Checksum Algorithm:",w.sizegroup)
            hbox.pack_start(w.algorithm_label,False,False,5)
            w.algorithm_combobox = Gtk.ComboBoxText()
            for i in sgbackup.config.CONFIG['config']['checksum.algorithm']['values']:
                w.algorithm_combobox.append(i,i)
            w.algorithm_combobox.set_active_id(sgbackup.config.CONFIG['checksum.algorithm'])
            hbox.pack_start(w.algorithm_combobox,True,True,5)
            listbox_add_widget(lb,hbox)
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            w.bsdtags_label = create_label('BSD Tags:',w.sizegroup)
            hbox.pack_start(w.bsdtags_label,False,False,5)
            w.bsdtags_switch = Gtk.Switch()
            w.bsdtags_switch.set_active(sgbackup.config.CONFIG['checksum.bsd-tags'])
            hbox.pack_end(w.bsdtags_switch,False,False,5)
            listbox_add_widget(lb,hbox)
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            w.check_label = create_label('Check internal checksums:',w.sizegroup)
            hbox.pack_start(w.check_label,False,False,5)
            w.check_switch = Gtk.Switch()
            w.check_switch.set_active(sgbackup.config.CONFIG['checksum.check'])
            hbox.pack_end(w.check_switch,False,False,5)
            listbox_add_widget(lb,hbox)
            
            w.add(lb)
            return w
        # ChecksumSettings.do_create_widget()
    # ChecksumSettings class
    
    class ChecksumPlugin(plugins.Plugin):
        def __init__(self):
            plugins.Plugin.__init__(self,PLUGIN_ID,'Checksum Plugin',
                                    version=sgbackup.config.version(),
                                    settings=ChecksumSettings(),
                                    sgbackup_plugin='checksum',
                                    sgbackup_plugin_enable=True,                                             
                                    menu={'file':MENU_FILE,'object':'checksum-menu'},
                                    gameview_menu={'file':MENU_FILE,'object':'checksum-gameview-menu'},
                                    backupview_menu={'file':MENU_FILE,'object':'checksum-backupview-menu'})
        # ChecksumPlugin.__init__()

        def has_checksum_file(self,backup_filename):
            algorithm = CONFIG['checksum.algorithm']
            return os.path.isfile('.'.join((backup_filename,algorithm)))
            
        def get_checksum_files(self,backup_filename):
            return checksum.find_checksum_files(backup_filename)
            
        def _on_action_check_all(self,action,data,appwindow):
            pass
            
        def _on_action_check_game(self,action,data,appwindow):
            pass
            
        def _on_action_check_backup(self,action,data,appwindow):
            pass
            
        def _on_action_create_all(self,action,data,appwindow):
            pass
            
        def _on_action_create_game(self,action,data,appwindow):
            pass
            
        def _on_action_create_backup(self,action,data,appwindow):
            pass
            
        def _on_gameview_selection_changed(self,selection,appwindow):
            model,iter = selection.get_selected()
            if iter:
                appwindow.action_checksum_check_game.set_enabled(True)
                appwindow.action_checksum_create_game.set_enabled(True)
            else:
                appwindow.action_checksum_check_game.set_enabled(False)
                appwindow.action_checksum_create_game.set_enabled(False)
        # ChecksumPlugin._on_gameview_selection_changed()
            
        def _on_backupview_selection_changed(self,selection,appwindow):
            model,iter = selection.get_selected()
            if iter:
                file = model.get_value(iter,appwindow.BV_COL_FILENAME)
                if self.has_checksum_file(file):
                    appwindow.action_checksum_create_backup.set_enabled(False)
                else:
                    appwindow.action_checksum_create_backup.set_enabled(True)
                    
                ckfiles = self.get_checksum_files(file)
                if ckfiles:
                    appwindow.action_checksum_check_backup.set_enabled(True)
                else:
                    appwindow.action_checksum_check_backup.set_enabled(False)
            else:
                appwindow.action_checksum_check_backup.set_enabled(False)
                appwindow.action_checksum_create_backup.set_enabled(False)
        # ChecksumPlugin._on_backupview_selection_changed()

        def do_enable(self,appwindow):
            db = sgbackup.database.Database()
            
            gv_model,gv_iter = appwindow.gameview.get_selection().get_selected()
            bv_model,bv_iter = appwindow.gameview.get_selection().get_selected()
            
            game=None
            backup_file = None
            if gv_iter:
                game = db.get_game(gv_model.get_value(gv_iter,appwindow.GV_COL_GAMEID))
            if bv_iter:
                backup_file = bv_model.get_value(bv_iter,appwindow.BV_COL_FILENAME)
            
            if not hasattr(appwindow,'action_checksum_check_all'):
                appwindow.action_checksum_check_all = Gio.SimpleAction.new('checksum-check-all',None)
                appwindow.action_checksum_check_all.connect('activate',self._on_action_check_all,appwindow)
                appwindow.add_action(appwindow.action_checksum_check_all)
            else:
                appwindow.action_checksum_check_all.set_enabled(True)
                
            if not hasattr(appwindow,'action_checksum_check_game'):
                appwindow.action_checksum_check_game = Gio.SimpleAction.new('checksum-check-game',None)
                appwindow.action_checksum_check_game.connect('activate',self._on_action_check_game,appwindow)
                appwindow.add_action(appwindow.action_checksum_check_game)
                if not gv_iter:
                    appwindow.action_checksum_check_game.set_enabled(False)
            else:
                appwindow.action_checksum_check_game.set_enabled(bool(gv_iter))
                
            if not hasattr(appwindow,'action_checksum_check_backup'):
                appwindow.action_checksum_check_backup = Gio.SimpleAction.new('checksum-check-backup',None)
                appwindow.action_checksum_check_backup.connect('activate',self._on_action_check_backup,appwindow)
                appwindow.add_action(appwindow.action_checksum_check_backup)
                enable = False
                if game and backup_filename:
                    cksums = self.get_checksum_files(backup_filename)
                    if cksums:
                        enable = True
                appwindow.action_checksum_check_backup.set_enabled(enable)                                                
            else:
                enable = False
                if game and backup_filename:
                    cksums = self.get_checksum_files(backup_filename)
                    if cksums:
                        enable = True
                appwindow.action_checksum_check_backup.set_enabled(enable)
                
            if not hasattr(appwindow,'action_checksum_create_all'):
                appwindow.action_checksum_create_all = Gio.SimpleAction.new('checksum-create-all',None)
                appwindow.action_checksum_create_all.connect('activate',self._on_action_create_all,appwindow)
                appwindow.add_action(appwindow.action_checksum_create_all)
            else:
                appwindow.action_checksum_create_all.set_enabled(True)
                
            if not hasattr(appwindow,'action_checksum_create_game'):
                appwindow.action_checksum_create_game = Gio.SimpleAction.new('checksum-create-game',None)
                appwindow.action_checksum_create_game.connect('activate',self._on_action_create_game,appwindow)
                appwindow.add_action(appwindow.action_checksum_create_game)
                appwindow.action_checksum_create_game.set_enabled(bool(gv_iter))
            else:
                appwindow.action_checksum_create_game.set_enabled(bool(gv_iter))
                
            if not hasattr(appwindow,'action_checksum_create_backup'):
                appwindow.action_checksum_create_backup = Gio.SimpleAction.new('checksum-create-backup',None)
                appwindow.action_checksum_create_game.connect('activate',self._on_action_create_backup,appwindow)
                appwindow.add_action(appwindow.action_checksum_create_backup)
                enable = False
                if game and backup_filename and not self.has_checksum_file(backup_filename):
                    enable = True
                appwindow.action_checksum_create_backup.set_enabled(enable)
            else:
                enable = False
                if game and backup_filename and not self.has_checksum_file(game,backup_filename):
                    enable = True
                appwindow.action_checksum_create_backup.set_enabled(enable)
                    
            if not hasattr(appwindow.gameview,'checksum_selection_changed_id'):
                id = appwindow.gameview.get_selection().connect('changed',self._on_gameview_selection_changed,appwindow)
                appwindow.gameview.checksum_selection_changed_id = id
    
            if not hasattr(appwindow.backupview,'checksum_selection_changed_id'):
                id = appwindow.backupview.get_selection().connect('changed',self._on_backupview_selection_changed,appwindow)
                appwindow.backupview.checksum_selection_changed_id = id
            
            db.close()
            plugins.Plugin.do_enable(self,appwindow)
        # ChecksumPlugin.do_enable()
        
        def do_disable(self,appwindow):
            if hasattr(appwindow,'action_checksum_check_all'):
                appwindow.action_checksum_check_all.set_enabled(False)
            if hasattr(appwindow,'action_checksum_check_backup'):
                appwindow.action_checksum_check_backup.set_enabled(False)
            if hasattr(appwindow,'action_checksum_check_game'):
                appwindow.action_checksum_check_game.set_enabled(False)
            if hasattr(appwindow,'action_checksum_create_all'):
                appwindow.action_checksum_create_all.set_enabled(False)
            if hasattr(appwindow,'action_checksum_create_backup'):
                appwindow.action_checksum_create_backup.set_enabled(False)
            if hasattr(appwindow,'action_checksum_create_game'):
                appwindow.action_checksum_create_game.set_enabled(False)
            if hasattr(appwindow.gameview,'checksum_selection_changed_id'):
                appwindow.gameview.get_selection().disconnect(appwindow.gameview.checksum_selection_changed_id)
                delattr(appwindow.gameview,'checksum_selection_changed_id')
            if hasattr(appwindow.backupview,'checksum_selection_changed_id'):
                appwindow.backupview.get_selection().disconnect(appwindow.backupview.checksum_selection_changed_id)
                delattr(appwindow.backupview,'checksum_selection_changed_id')
                
            plugins.Plugin.do_disable(self,appwindow)
        # ChecksumPlugin.do_disable()
    # ChecksumPlugin class
    
    plugin = ChecksumPlugin()

