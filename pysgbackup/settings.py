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

import sgbackup
from sgbackup.config import CONFIG
from functools import cmp_to_key
import string
import os
import sys
import pysgbackup

SETTINGS = {
}
    
class SettingsDialog(Gtk.Dialog):
    __gsignals__ = {
        'save-settings': (GObject.SIGNAL_RUN_FIRST,None,()),
        'plugin-enable': (GObject.SIGNAL_RUN_FIRST,None,(str,str)),
        'plugin-disable': (GObject.SIGNAL_RUN_FIRST,None,(str,str))
    }
        
    def __init__(self,parent=None):
        Gtk.Dialog.__init__(self,parent=parent)
        self.set_title('PySGBackup: Settings')
        self.__settings = {}
        
        self.__parent = parent
        
        vbox = self.get_content_area()
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_default_size(600,400)
        
        # create_content_area
        self.content = Gtk.Stack()
        self.paned.pack2(self.content,True,True)
        
        self.settings_app = self.__create_app_settings()
        self.content.add_titled(self.settings_app,'app','App Settings')
        
        self.settings_generic = self.__create_generic_settings()
        self.content.add_titled(self.settings_generic,'generic','Generic Settings')
        
        self.settings_backup = self.__create_backup_settings()
        self.content.add_titled(self.settings_backup,'backup','Backup Settings')
        
        self.settings_plugins = self.__create_plugin_settings()
        self.content.add_titled(self.settings_plugins,'plugins','Plugins')
        
        for sid,settings in SETTINGS.items():
            settings.load(self)
            widget = settings.get_widget()
            if settings.id and settings.title and widget:
                self.content.add_titled(widget,settings.id,settings.title)
                self.__settings[sid] = settings
                self.connect('destroy',settings.unload)
                
                if settings.attribute:
                    try:
                        setattr(self,settings.attribute,widget)
                    except Exception as error:
                        print('!!! ERROR !!! {}'.format(error),file=sys.stderr)
            settings.load(self)
            
        self.chooser=Gtk.StackSidebar()
        self.chooser.set_stack(self.content)
        self.paned.add1(self.chooser)
        
        self.vbox.pack_start(self.paned,True,True,0)
        
        self.add_button('Apply',Gtk.ResponseType.APPLY)
        self.add_button('Cancel',Gtk.ResponseType.CANCEL)
        
        self.show_all()
        
    @GObject.Property
    def settings(self):
        return self.__settings
    
    @GObject.Property
    def parent(self):
        return self.__parent
        
    def __create_app_settings(self):
        def create_label(text,sizegroup):
            l = Gtk.Label(text)
            l.set_xalign(0.0)
            sizegroup.add_widget(l)
            return l
        # create_label()
        
        def listbox_add(listbox,widget):
            row = Gtk.ListBoxRow()
            row.add(widget)
            listbox.add(row)
        # listbox_add
        
        w = Gtk.ScrolledWindow()
        w.sizegroup = Gtk.SizeGroup()
        w.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
        lb = Gtk.ListBox()
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(create_label('GameView| Show Database ID:',w.sizegroup),False,False,5)
        w.dbid_switch = Gtk.Switch()
        w.dbid_switch.set_active(CONFIG['pysgbackup.gameview.show-id'])
        hbox.pack_end(w.dbid_switch,False,False,0)
        listbox_add(lb,hbox)
            
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(create_label('GameView| Show GameIDs:',w.sizegroup),False,False,5)
        w.gameid_switch = Gtk.Switch()
        w.gameid_switch.set_active(CONFIG['pysgbackup.gameview.show-gameid'])
        hbox.pack_end(w.gameid_switch,False,False,0)
        listbox_add(lb,hbox)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(create_label('GameView| Show Final:',w.sizegroup),False,False,5)
        w.final_switch = Gtk.Switch()
        w.final_switch.set_active(CONFIG['pysgbackup.gameview.show-final'])
        hbox.pack_end(w.final_switch,False,False,0)
        listbox_add(lb,hbox)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(create_label('GameView| Show Steam-AppIDs:',w.sizegroup),False,False,5)
        w.steam_appid_switch = Gtk.Switch()
        w.steam_appid_switch.set_active(CONFIG['pysgbackup.gameview.show-steam-appid'])
        hbox.pack_end(w.steam_appid_switch,False,False,0)
        listbox_add(lb,hbox)
        
        w.add(lb)
        return w
                 
    def __create_generic_settings(self):
        def create_label(text):
            l = Gtk.Label(text)
            l.set_justify(Gtk.Justification.LEFT)
            l.set_halign(Gtk.Align.START)
            l.set_xalign(0.0)
            
            return l
        # create_label()
        
        def _on_db_button_clicked(button,widget):
            t = string.Template(widget.database_entry.get_text())
            path = t.substitute(sgbackup.config.get_template_vars())
            
            dialog = Gtk.FileChooserDialog('Set Game-Database',self,Gtk.FileChooserAction.SAVE)
            dialog.add_button('Accept',Gtk.ResponseType.ACCEPT)
            dialog.add_button('Cancel',Gtk.ResponseType.CANCEL)
            dialog.set_create_folders(True)
            dialog.set_current_folder(os.path.dirname(path))
            dialog.set_current_name(os.path.basename(path))
            result = dialog.run()
            dialog.hide()
            dialog.destroy()            
            if result == Gtk.ResponseType.ACCEPT:
                widget.database_entry.set_text(dialog.get_filename())
                widget.database_entry.show()            
        # _on_db_button_clicked()
                
        def _on_gameconf_button_clicked(button,widget):
            t = string.Template(widget.gameconf_entry.get_text())
            path = t.substitute(sgbackup.config.get_template_vars())
            
            dialog = Gtk.FileChooserDialog('Set Gameconf directory',self,Gtk.FileChooserAction.SELECT_FOLDER)
            dialog.add_button('Accept',Gtk.ResponseType.ACCEPT)
            dialog.add_button('Cancel',Gtk.ResponseType.CANCEL)
            dialog.set_create_folders(True)
            dialog.set_current_folder(path)
            result = dialog.run()
            dialog.hide()
            if result == Gtk.ResponseType.ACCEPT:
                widget.gameconf_entry.set_text(dialog.get_filename())
                widget.gameconf_entry.show()
            dialog.destroy()
        # _on_gameconf_button_clicked()
        
        def _on_archivers_button_clicked(button,widget):
            t = string.Template(widget.archivers_entry.get_text())
            path = t.substitute(sgbackup.config.get_template_vars())
            
            dialog = Gtk.FileChooserDialog('Set Archivers directory',self,Gtk.FileChooserAction.SELECT_FOLDER)
            dialog.add_button('Accept',Gtk.ResponseType.ACCEPT)
            dialog.add_button('Cancel',Gtk.ResponseType.CANCEL)
            dialog.set_create_folders(True)
            dialog.set_current_folder(path)
            result = dialog.run()
            dialog.hide()
            if result == Gtk.ResponseType.ACCEPT:
                widget.archivers_entry.set_text(dialog.get_filename())
                widget.archivers_entry.show()
            dialog.destroy()
        # _on_archivers_button_clicked
        
        w = Gtk.ScrolledWindow()
        lb = Gtk.ListBox()
        w.sizegroup = Gtk.SizeGroup()
        w.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = create_label('Verbose Messages:')
        w.sizegroup.add_widget(label)
        hbox.pack_start(label,False,False,5)
        w.verbose_switch = Gtk.Switch()
        w.verbose_switch.set_active(CONFIG['verbose'])
        hbox.pack_end(w.verbose_switch,False,False,0)
        row = Gtk.ListBoxRow()
        row.add(hbox)
        lb.add(row)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)        
        label = create_label('Games Database:')
        w.sizegroup.add_widget(label)
        hbox.pack_start(label,False,False,5)
        w.database_entry = Gtk.Entry()
        if 'database.template' in CONFIG:
            w.database_entry.set_text(CONFIG['database.template'])
        else:
            w.database_entry.set_text(CONFIG['database'])
        hbox.pack_start(w.database_entry,True,True,0)
        button = Gtk.Button.new_from_icon_name('document-open',Gtk.IconSize.BUTTON)
        button.connect('clicked',_on_db_button_clicked,w)
        hbox.pack_start(button,False,False,0)
        row = Gtk.ListBoxRow()
        row.add(hbox)
        lb.add(row)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = create_label('Gameconf directory:')
        w.sizegroup.add_widget(label)
        hbox.pack_start(label,False,False,5)
        w.gameconf_entry = Gtk.Entry()
        if 'user-gameconf-dir.template' in CONFIG:
            w.gameconf_entry.set_text(CONFIG['user-gameconf-dir.template'])
        else:
            w.gameconf_entry.set_text(CONFIG['user-gameconf-dir'])
        hbox.pack_start(w.gameconf_entry,True,True,0)
        button = Gtk.Button.new_from_icon_name('document-open',Gtk.IconSize.BUTTON)
        button.connect('clicked',_on_gameconf_button_clicked,w)
        hbox.pack_start(button,False,False,0)
        row = Gtk.ListBoxRow()
        row.add(hbox)
        lb.add(row)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = create_label('Archivers directory:')
        w.sizegroup.add_widget(label)
        hbox.pack_start(label,False,False,5)
        w.archivers_entry = Gtk.Entry()
        if 'user-archivers-dir.template' in CONFIG:
            w.archivers_entry.set_text(CONFIG['user-archivers-dir.template'])
        else:
            w.archivers_entry.set_text(CONFIG['user-archivers-dir'])
        hbox.pack_start(w.archivers_entry,True,True,0)
        button = Gtk.Button.new_from_icon_name('document-open',Gtk.IconSize.BUTTON)
        button.connect('clicked', _on_archivers_button_clicked,w)
        hbox.pack_start(button,False,False,0)
        row = Gtk.ListBoxRow()
        row.add(hbox)
        lb.add(row)
        
        w.add(lb)
        return w
    # __create_generic_settings()
        
    def __create_backup_settings(self):
        def create_label(text,sizegroup=None):
            l = Gtk.Label(text)
            l.set_justify(Gtk.Justification.LEFT)
            l.set_halign(Gtk.Align.START)
            l.set_xalign(0.0)
            
            if sizegroup:
                sizegroup.add_widget(l)
            return l
        # create_label()
        
        def listbox_add(listbox,widget):
            row = Gtk.ListBoxRow()
            row.add(widget)
            listbox.add(row)
        # listbox_add()
        
        def _on_backupdir_button_clicked(button,widget):
            t = string.Template(widget.backupdir_entry.get_text())
            path = t.substitute(sgbackup.config.get_template_vars())
            
            dialog = Gtk.FileChooserDialog("Select Backupdir",self,Gtk.FileChooserAction.SELECT_FOLDER)
            dialog.set_create_folders(True)
            dialog.set_current_folder(path)
            dialog.add_button('Accept',Gtk.ResponseType.ACCEPT)
            dialog.add_button('Cancel',Gtk.ResponseType.CANCEL)
            
            result = dialog.run()
            dialog.hide()
            
            if result == Gtk.ResponseType.ACCEPT:
                widget.backupdir_entry.set_text(dialog)
                widget.backupdir_entry.show()
            dialog.destroy()
        # _on_backupdir_button_clicked()
        
        def _on_listfile_button_clicked(button,widget):
            t = string.Template(widget.listfile_entry.get_text())
            path = t.substitute(sgbackup.config.get_template_vars())
            
            dialog = Gtk.FileChooserDialog("Select Listfile",self,Gtk.FileChooserAction.SAVE)
            dialog.set_create_folders(True)
            dialog.set_current_folder(os.path.dirname(path))
            dialog.set_current_name(os.path.basename(path))
            dialog.add_button('Accept',Gtk.ResponseType.ACCEPT)
            dialog.add_button('Cancel',Gtk.ResponseType.CANCEL)
            
            result = dialog.run()
            dialog.hide()
            if result == Gtk.ResponseType.ACCEPT:
                widget.listfile_entry.set_text(dialog.get_filename())
                widget.listfile_entry.show()
            dialog.destroy()
        # _on_listfile_button_clicked
        
        def _on_zipfile_compression_combobox_changed(combo,widget):
            compression = combo.get_active_id()
            compresslevel = w.zipfile_compresslevel_spinbutton.get_value_as_int()
            
            if  compression == 'deflated':
                adjustment = Gtk.Adjustment(float(compresslevel),0.0,10.0,1.0,1.0,1.0)
                w.zipfile_compresslevel_spinbutton.set_sensitive(True)
            elif compression == 'bzip2':
                adjustment = Gtk.Adjustment(float(compresslevel),1.0,10.0,1.0,1.0,1.0)
                w.zipfile_compresslevel_spinbutton.set_sensitive(True)
            else:
                adjustment = Gtk.Adjustment(float(compresslevel),0.0,1.0,1.0,1.0,1.0)
                w.zipfile_compresslevel_spinbutton.set_sensitive(False)
                
            w.zipfile_compresslevel_spinbutton.configure(adjustment,1.0,0)
            w.zipfile_compresslevel_spinbutton.show()
        # _on_zipfile_compression_combobox_changed()
                    
        w = Gtk.ScrolledWindow()
        lb = Gtk.ListBox()
        w.sizegroup = Gtk.SizeGroup()
        w.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(create_label('Backup directory:',w.sizegroup),False,False,5)
        w.backupdir_entry = Gtk.Entry()
        if 'backup.dir.template' in CONFIG:
            w.backupdir_entry.set_text(CONFIG['backup.dir.template'])
        else:
            w.backupdir_entry.set_text(CONFIG['backup.dir'])
        hbox.pack_start(w.backupdir_entry,True,True,5)
        button = Gtk.Button.new_from_icon_name('document-open',Gtk.IconSize.BUTTON)
        button.connect('clicked',_on_backupdir_button_clicked,w)
        hbox.pack_start(button,False,False,5)
        listbox_add(lb,hbox)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(create_label('Checksum Algorithm:',w.sizegroup),False,False,5)
        w.checksum_cbox = Gtk.ComboBoxText()
        model = w.checksum_cbox.get_model()
        for i in sorted(CONFIG['backup.checksum.values']):
            model.append([i,i])
        w.checksum_cbox.set_active_id(CONFIG['backup.checksum'])
        hbox.pack_start(w.checksum_cbox,True,True,5)
        listbox_add(lb,hbox)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(create_label('Archiver:',w.sizegroup),False,False,5)
        w.archiver_cbox = Gtk.ComboBoxText()
        model = w.archiver_cbox.get_model()
        for i in sgbackup.archivers.ARCHIVERS.keys():
            model.append([i,i])
        w.archiver_cbox.set_active_id(CONFIG['backup.archiver'])
        hbox.pack_start(w.archiver_cbox,True,True,5)
        listbox_add(lb,hbox)
                
        listbox_add(lb,Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(create_label('Zipfile Compression:',w.sizegroup),False,False,5)
        w.zipfile_compression_combo = Gtk.ComboBoxText()
        zf_compression = {}
        for k,v in CONFIG['zipfile.compression.values'].items():
            w.zipfile_compression_combo.append(k,k)
            zf_compression[v] = k
        w.zipfile_compression_combo.set_active_id(zf_compression[CONFIG['zipfile.compression']])
        w.zipfile_compression_combo.connect('changed', _on_zipfile_compression_combobox_changed,w)
        hbox.pack_start(w.zipfile_compression_combo,True,True,5)
        listbox_add(lb,hbox)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hbox.pack_start(create_label('Zipfile Compresslevel:',w.sizegroup),False,False,5)
        if zf_compression[CONFIG['zipfile.compression']] == 'deflated':
            adjustment = Gtk.Adjustment.new(float(CONFIG['zipfile.compresslevel']),0.0,10.0,1.0,1.0,1.0)
        elif zf_compression[CONFIG['zipfile.compression']] == 'bzip2':
            adjustment = Gtk.Adjustment.new(float(CONFIG['zipfile.compresslevel']),1.0,10.0,1.0,1.0,1.0)
        else:
            adjustment = Gtk.Adjustment.new(float(CONFIG['zipfile.compresslevel']),0.0,1.0,1.0,1.0,1.0)
        w.zipfile_compresslevel_spinbutton = Gtk.SpinButton.new(adjustment,1.0,0)
        
        if zf_compression[CONFIG['zipfile.compression']] not in ['deflated','bzip2']:
            w.zipfile_compresslevel_spinbutton.set_sensitive(False)
        hbox.pack_start(w.zipfile_compresslevel_spinbutton,True,True,5)
        listbox_add(lb,hbox)
            
        w.add(lb)
        return w
    # __create_backup_settings()
    
    def __create_plugin_settings(self):
        def keycompare(x,y):
            def get_real_key(k):
                x = k.split(':',1)
                if len(x) > 1:
                    return x[1]
                return x
            # get_real_key()
            
            k0 = get_real_key(x)
            k1 = get_real_key(y)
            
            if k0 < k1:
                return -1
            if k0 == k1:
                return 0
            return 1
        # keycompare()
                    
        w = Gtk.ScrolledWindow()
        lb = Gtk.ListBox()
        w.plugins = []
        w.plugin_switches = {}
        
        for k in sgbackup.plugins.PLUGINS.keys():
            key='sgbackup:{}'.format(k)
            w.plugins.append(key)
        
        for k,p in pysgbackup.plugins.PLUGINS.items():
            key='pysgbackup:{}'.format(k)
            if p.sgbackup_plugin and p.sgbackup_plugin_enable:
                sgbackup_key = 'sgbackup:{}'.format(p.sgbackup_plugin.name)
                for i in range(len(w.plugins)):
                    if w.plugins[i] == sgbackup_key:
                        del w.plugins[i]
                        break
            w.plugins.append(key)
            
        w.plugins = sorted(w.plugins,key=cmp_to_key(keycompare))
        
        for i in w.plugins:
            hbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
            vbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL)
            engine,plugin_id = i.split(':',1)
            
            plugin = None
            if engine == 'sgbackup':
                plugin = sgbackup.plugins.PLUGINS[plugin_id]
                title = plugin.name
            elif engine == 'pysgbackup':
                plugin = pysgbackup.plugins.PLUGINS[plugin_id]
                title = plugin.title
                
            if plugin:
                if engine == 'pysgbackup':
                    if plugin.icon:
                        if 'icon-name' in plugin.icon:
                            icon = Gtk.Image.new_from_icon_name(plugin.icon['icon-name'],Gtk.IconSize.LARGE_TOOLBAR)
                        elif 'file' in plugin.icon:
                            icon = Gtk.Image.new_from_file(plugin.icon['file'])
                        elif 'pixbuf' in plugin.icon:
                            icon = Gtk.Image.new_from_pixbuf(plugin.icon['pixbuf'])
                        else:
                            icon = Gtk.Image.new_from_icon_name('applications-system-symbolic',Gtk.IconSize.LARGE_TOOLBAR)
                    else:
                        icon = Gtk.Image.new_from_icon_name('applications-system-symbolic',Gtk.IconSize.LARGE_TOOLBAR)
                else:
                    icon = Gtk.Image.new_from_icon_name('applications-system-symbolic',Gtk.IconSize.LARGE_TOOLBAR)
                description = plugin.description
                
                hbox.pack_start(icon,False,False,5)
                
                title_label = Gtk.Label("<span weight='bold' size='large'>" + title + "</span>")
                title_label.set_use_markup(True)
                title_label.set_xalign(0.0)
                vbox.pack_start(title_label,False,False,0)
                label = Gtk.Label(description)
                label.set_xalign(0.0)
                vbox.pack_start(label,False,False,0)
                
                hbox.pack_start(vbox,True,True,5)
                
                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
                switch = Gtk.Switch()
                switch.set_active(plugin.enabled)
                vbox.pack_start(switch,False,False,0)
                hbox.pack_end(vbox,False,False,5)
                w.plugin_switches[i] = switch
            
                row = Gtk.ListBoxRow()
                row.add(hbox)
                lb.add(row)
        w.add(lb)
        return w
    # SettingsDialog.__create_plugin_settings()
    
    def save_settings(self):
        self.emit('save-settings')
        filename = CONFIG['user-config']
        sgbackup.config.write_config(filename,False)
        
    def plugin_enable(self,engine,plugin_id):
        pid = "{}:{}".format(engine,plugin_id)
        if pid in self.settings_plugins.plugin_switches:
            switch = self.settings_plugins.plugin_switches[pid]
            if not switch.get_active():
                switch.set_active(True)
                            
        self.emit('plugin-enable',engine,plugin_id)
    
    def plugin_disable(self,engine,plugin_id):
        pid = "{}:{}".format(engine,plugin_id)
        if pid in self.settings_plugins.plugin_switches:
            switch = self.settings_plugins.plugin_switches[pid]
            if switch.get_active():
                switch.set_active(False)
                
        self.emit('plugin-disable',engine,plugin_id)
        
    def do_save_settings(self):
        app = self.settings_app
        generic = self.settings_generic
        backup = self.settings_backup
        
        if isinstance(self.parent,pysgbackup.AppWindow):
            appwindow = self.parent
        else:
            appwindow = pysgbackup.application.appwindow
        
        #BEGIN: Enable disable plugins
        for i in self.settings_plugins.plugins:
            try:
                engine,pid = i.split(':',1)
            except Exception as error:
                print(error,file=sys.stderr)
                continue
            
            if engine == 'pysgbackup':
                if pid in pysgbackup.plugins.PLUGINS: 
                    plugin = pysgbackup.plugins.PLUGINS[pid]
                else:
                    continue
            elif engine == 'sgbackup':
                if pid in sgbackup.plugins.PLUGINS:
                    plugin = sgbackup.plugins.PLUGINS[pid]
                else:
                    continue
            else:
                continue
                
            if i in self.settings_plugins.plugin_switches:
                plugin_switch = self.settings_plugins.plugin_switches[i]
                if plugin_switch.get_active() and not plugin.enabled:
                    self.plugin_enable(engine,pid)
                elif not plugin_switch.get_active() and plugin.enabled:
                    self.plugin_disable(engine,pid)
        #END: Enable/Disable plugins         
        
        CONFIG['verbose'] = generic.verbose_switch.get_active()
        
        CONFIG['backup.dir.template'] = self.settings_backup.backupdir_entry.get_text()
        t = string.Template(backup.backupdir_entry.get_text())
        CONFIG['backup.dir'] = t.substitute(sgbackup.config.get_template_vars())
        
        CONFIG['database.template'] = generic.database_entry.get_text()
        t = string.Template(generic.database_entry.get_text())
        CONFIG['database'] = t.substitute(sgbackup.config.get_template_vars())
        
        CONFIG['user-gameconf-dir.template'] = generic.gameconf_entry.get_text()
        t = string.Template(generic.gameconf_entry.get_text())
        CONFIG['user-gameconf-dir'] = t.substitute(sgbackup.config.get_template_vars())
        
        CONFIG['user-archivers-dir.template'] = generic.archivers_entry.get_text()
        t = string.Template(generic.archivers_entry.get_text())
        CONFIG['user-archivers-dir'] = t.substitute(sgbackup.config.get_template_vars())
        
        CONFIG['backup.checksum'] = backup.checksum_cbox.get_active_id()
        CONFIG['backup.archiver'] = backup.archiver_cbox.get_active_id()
        
        CONFIG['zipfile.compression'] = CONFIG['zipfile.compression.values'][backup.zipfile_compression_combo.get_active_id()]
        CONFIG['zipfile.compresslevel'] = backup.zipfile_compresslevel_spinbutton.get_value_as_int()
        
        CONFIG['pysgbackup.gameview.show-id'] = app.dbid_switch.get_active()
        pysgbackup.application.appwindow.gameview.column_id.set_visible(app.dbid_switch.get_active())
        
        CONFIG['pysgbackup.gameview.show-gameid'] = app.gameid_switch.get_active()
        pysgbackup.application.appwindow.gameview.column_gameid.set_visible(app.gameid_switch.get_active())
        
        CONFIG['pysgbackup.gameview.show-final'] = app.final_switch.get_active()
        pysgbackup.application.appwindow.gameview.column_final.set_visible(app.final_switch.get_active())
        
        CONFIG['pysgbackup.gameview.show-steam-appid'] = app.steam_appid_switch.get_active()
        pysgbackup.application.appwindow.gameview.column_steam_appid.set_visible(app.steam_appid_switch.get_active())
        
        for settings in self.settings.values():
            settings.save(self)
    # do_save_settings()
    
    
    def do_plugin_enable(self,engine,plugin_id):
        if isinstance(self.parent,pysgbackup.AppWindow):
            appwindow = self.parent
        else:
            appwindow = pysgbackup.application.appwindow
            
        db = sgbackup.database.Database()
            
        if engine == "sgbackup":
            if plugin_id in sgbackup.plugins.PLUGINS:
                p = sgbackup.plugins.PLUGINS[plugin_id]
                p.enable()
                db.enable_plugin(p.name)
            else:
                db.close()
                raise LookupError('Unable to lookup sgbackup-plugin "{0}"!'.format(plugin_id))
        elif engine == "pysgbackup":
            if plugin_id in pysgbackup.plugins.PLUGINS:
                p = pysgbackup.plugins.PLUGINS[plugin_id]
                p.enable(appwindow)
                db.enable_pysgbackup_plugin(p.name)
            else:
                db.close()
                raise LookupError('Unable to lookup pysgbackup-plugin "{0}"!'.format(plugin_id))
        else:
            db.close()
            raise ValueError('Unknown plugin engine "{0}"!'.format(engine))
        db.close()
    # SettingsDialog.do_plugin_enable()
    
    def do_plugin_disable(self,engine,plugin_id):
        if isinstance(self.parent,pysgbackup.AppWindow):
            appwindow = self.parent
        else:
            appwindow = pysgbackup.application.appwindow
            
        db = sgbackup.database.Database()
        
        if engine == "sgbackup":
            if plugin_id in sgbackup.plugins.PLUGINS:
                p = sgbackup.plugins.PLUGINS[plugin_id]
                p.disable()
                db.disable_plugin(p.name)
            else:
                db.close()
                raise LookupError('Unable to lookup sgbackup-plugin "{0}"!'.format(plugin_id))
        elif engine == "pysgbackup":
            if plugin_id in pysgbackup.plugins.PLUGINS:
                p = pysgbackup.plugins.PLUGINS[plugin_id]
                p.disable(appwindow)
                db.disable_pysgbackup_plugin(p.name)
            else:
                db.close()
                raise LookupError('Unable to lookup pysgbackup-plugin "{0}"!'.format(plugin_id))
        else:
            db.close()
            raise ValueError('Unknown plugin engine "{0}"!'.format(engine))
        db.close()
    # SettingsDialog.do_plugin_disable()
# SettingsDialog class
                
class Settings(GObject.GObject):
    __gsignals__ = {
        'load': (GObject.SIGNAL_RUN_FIRST,None,(SettingsDialog,)),
        'unload': (GObject.SIGNAL_RUN_FIRST,None,(SettingsDialog,)),
        'save': (GObject.SIGNAL_RUN_FIRST,None,(SettingsDialog,))
    }
    
    def __init__(self,id,title,
                 create_widget_callback=None,
                 attribute=None,
                 load_callback=None,
                 unload_callback=None,
                 save_callback=None):
                 
        GObject.GObject.__init__(self)
        
        self.__id = id
        self.__title = title
        self.__widget = None
        self.__attribute = attribute
        self.__load_cb = load_callback
        self.__unload_cb = unload_callback
        self.__save_cb = save_callback
        self.__create_widget_cb = create_widget_callback
        
    @GObject.Property
    def id(self):
        return self.__id
        
    @GObject.Property
    def title(self):
        return self.__title
        
    @GObject.Property
    def attribute(self):
        return self.__attribute
        
    @GObject.Property
    def parent(self):
        return self.__parent
        
    def get_widget(self):
        return self.__widget
              
    def set_widget(self,widget):
        #if not isinstance(widget,Gtk.Widget) or widget is not None:
        #    raise TypeError('widget')
        self.__widget = widget
        
    def load(self,settings_dialog):
        self.emit('load',settings_dialog)
        
    def unload(self,settings_dialog):
        self.emit('unload',settings_dialog)
    
    def save(self,settings_dialog):
        self.emit('save',settings_dialog)
        
    def do_create_widget(self,settings_dialog):
        if self.__create_widget_cb and callable(self.__create_widget_cb):
            return self.__create_widget_cb(self)
        return None

    def do_load(self,settings_dialog):
        self.__widget = self.do_create_widget(settings_dialog)
        if self.__load_cb and callable(self.__load_cb):
            self.__load_cb(self,settings_dialog)
            
    def do_unload(self,settings_dialog):
        if self.__widget:
            self.__widget = None
            
        if self.__unload_cb and callable(self.__unload_cb):
            self.__unload_cb(self,settings_dialog) 
                       
    def do_save(self,settings_dialog):
        if self.__save_cb and callable(self.__save_cb):
            self.__save_cb(self,settings_dialog)
# Settings class
