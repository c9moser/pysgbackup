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
        
        self.settings_generic = self.__create_generic_settings()
        
        
        self.content.add_titled(self.settings_generic,'generic','Generic Settings')
                
        
        self.chooser=Gtk.StackSidebar()
        self.chooser.set_stack(self.content)
        self.paned.add1(self.chooser)
        
        
        self.vbox.pack_start(self.paned,True,True,0)
        
        self.add_button('Apply',Gtk.ResponseType.APPLY)
        self.add_button('Cancel',Gtk.ResponseType.CANCEL)
        
        self.show_all()
        
    def __create_generic_settings(self):
        def create_label(text):
            l = Gtk.Label(text)
            l.set_justify(Gtk.Justification.LEFT)
            l.set_halign(Gtk.Align.START)
            l.set_xalign(0.0)
            
            return l
            
        def _on_db_button_clicked(button,widget):
            t = string.Template(widget.database_entry.get_text())
            v = sgbackup.config.get_template_vars()
            path = t.substitute(v)
            
            dialog = Gtk.FileChooserDialog('Set Game-Database',
                                           self,
                                           Gtk.FileChooserAction.SAVE)
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
            pass
        # _on_gameconf_button_clicked()
        
        def _on_archivers_button_clicked(button,widget):
            pass
        # _on_archivers_button_clicked
        
        w = Gtk.ScrolledWindow()
        lb = Gtk.ListBox()
        w.sizegroup = Gtk.SizeGroup()
        w.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        label = create_label('Verbose Messages:')
        w.sizegroup.add_widget(label)
        hbox.pack_start(label,False,False,0)
        w.verbose_switch = Gtk.Switch()
        w.verbose_switch.set_active(CONFIG['verbose'])
        hbox.pack_start(w.verbose_switch,False,False,0)
        row = Gtk.ListBoxRow()
        row.add(hbox)
        lb.add(row)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)        
        label = create_label('Games Database:')
        w.sizegroup.add_widget(label)
        hbox.pack_start(label,False,False,0)

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
        hbox.pack_start(label,False,False,0)
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
        hbox.pack_start(label,False,False,0)
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
        
    def save_settings(self):
        self.emit('save-settings')
        #TODO write_config
        
    def do_save_settings(self):
        CONFIG['verbose'] = self.settings_generic.verbose_switch.get_active()
        

