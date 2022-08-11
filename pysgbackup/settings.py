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

def _create_generic_settings_widget(dialog):
    def on_save_config(dialog,config,widget):
        config['verbose'] = widget.verbose_switch.get_active()
    
    
    w = Gtk.ScrolledWindow()
    w.grid = Gtk.Grid()
    label = Gtk.Label('Verbose:')
    w.grid.attach(label,0,0,1,1)
    w.verbose_switch = Gtk.Switch()
    w.verbose_switch.set_active(CONFIG['verbose'])
    
    return w

SETTINGS = {
}

class SettingsDialog(Gtk.Dialog):
    __gsignals__ = {
        'save-settings': (GObject.SIGNAL_RUN_CLEANUP,None,[])
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
        
        self.settings_generic = Gtk.ScrolledWindow()
        grid = Gtk.Grid()
        label = Gtk.Label('Verbose Messages:')
        grid.attach(label, 0,0,1,1)
        self.settings_generic.verbose_switch = Gtk.Switch()
        self.settings_generic.verbose_switch.set_active(CONFIG['verbose'])
        grid.attach(self.settings_generic.verbose_switch,1,0,1,1)
        self.settings_generic.add(grid)
        self.content.add_titled(self.settings_generic,'generic','Generic Settings')
                
        
        self.chooser=Gtk.StackSidebar()
        self.chooser.set_stack(self.content)
        self.paned.add1(self.chooser)
        
        
        self.vbox.pack_start(self.paned,True,True,0)
        
        self.add_button('Apply',Gtk.ResponseType.APPLY)
        self.add_button('Cancel',Gtk.ResponseType.CANCEL)    
        
        self.show_all()
        
    def save_settings(self):
        self.emit('save-settings')
        
    def do_save_settings(self):
        CONFIG['verbose'] = self.settings_generic.verbose_switch.get_active()
        

