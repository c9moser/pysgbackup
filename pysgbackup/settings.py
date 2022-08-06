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
from gi.repository import Gtk,GLib

class SettingsDialog(Gtk.Dialog):
    def __init__(self,parent=None):
        Gtk.Dialog.__init__(self,parent=parent)
        self.set_title('PySGBackup: Settings')
        
        vbox = self.get_content_area()
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        
        # create_chooser
        #TODO
        
        # create_content_area
        #TODO
        
        self.add_button('Apply',Gtk.ResponseType.APPLY)
        self.add_button('Cancel',Gtk.ResponseType.CANCEL)
    
    def _save_settings(self):
        pass
        
    def do_response(self,response):
        if response == Gtk.ResponseType.APPLY:
            self._save_settings()
            
        if response in [Gtk.ResponseType.CANCEL,Gtk.ResponseType.APPLY]:
            self.hide()
            self.destroy()
            
            
