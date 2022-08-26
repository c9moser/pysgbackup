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
import string
import os
import pysgbackup

SETTINGS = {
}

class SettingsDialog(Gtk.Dialog):
    __gsignals__ = {
        'save-settings': (GObject.SIGNAL_RUN_FIRST,None,[])
    }
    
    (
        CHOOSER_COL_ID,
        CHOOSER_COL_ICON_NAME,
        CHOOSER_COL_ICON_FILE,
        CHOOSER_COL_NAME
    ) = range(4)
    
    def __init__(self,parent=None):
        Gtk.Dialog.__init__(self,parent=parent)
        self.set_title('PySGBackup: Settings')
        
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
        
        self.chooser=Gtk.StackSidebar()
        self.chooser.set_stack(self.content)
        self.paned.add1(self.chooser)
        
        
        self.vbox.pack_start(self.paned,True,True,0)
        
        self.add_button('Apply',Gtk.ResponseType.APPLY)
        self.add_button('Cancel',Gtk.ResponseType.CANCEL)
        
        self.show_all()
        
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
    
    def save_settings(self):
        self.emit('save-settings')
        filename = CONFIG['user-config']
        sgbackup.config.write_config(filename,False)
        
    def do_save_settings(self):
        app = self.settings_app
        generic = self.settings_generic
        backup = self.settings_backup
        
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
        pysgbackup.app.appwindow.gameview.column_id.set_visible(app.dbid_switch.get_active())
        
        CONFIG['pysgbackup.gameview.show-gameid'] = app.gameid_switch.get_active()
        pysgbackup.app.appwindow.gameview.column_gameid.set_visible(app.gameid_switch.get_active())
        
        CONFIG['pysgbackup.gameview.show-final'] = app.final_switch.get_active()
        pysgbackup.app.appwindow.gameview.column_final.set_visible(app.final_switch.get_active())
        
        CONFIG['pysgbackup.gameview.show-steam-appid'] = app.steam_appid_switch.get_active()
        pysgbackup.app.appwindow.gameview.column_steam_appid.set_visible(app.steam_appid_switch.get_active())
                

