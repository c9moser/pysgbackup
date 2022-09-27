#-*- coding:utf-8 -*-
################################################################################
# pysgbackup.plugins.mkiso
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

import sgbackup.plugins.mkiso as mkiso

if mkiso.plugin:
    from gi.repository import Gtk,GLib,GObject
    from sgbackup.config import CONFIG
    import pysgbackup
    from pysgbackup.settings import Settings
    from pysgbackup.plugins import Plugin
    
    class MkisoSettings(Settings):
        def __init__(self):
            Settings.__init__(self,'mkiso',attribute='settings_mkiso')
            
        def _on_directory_button_clicked(self,button,widget):
            pass
            
        def do_create_widget(self):
            def lb_add_hbox(listbox,label,widget,sizegroup=None):
                hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                l = Gtk.Label(label)
                if (sizegroup):
                    sizegroup.add_widget(l)
                hbox.pack_start(l,False,False,5)
                hbox.pack_start(widget,True,True,5)
                lb_row = Gtk.ListBoxRow()
                lb_row.add(hbox)
                listbox.add(lb_row)
                
            w = Gtk.ScrolledWindow()
            w.sizegroup = Gtk.SizeGroup()
            w.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)    
            lb = Gtk.ListBox()
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            w.directory_entry = Gtk.Entry()
            w.directory_entry.set_text(CONFIG['mkiso.directory'])
            hbox.pack_start(w.directory_entry,True,True,0)
            w.directory_button = Gtk.Button.new_from_icon_name('document-open')
            w.directory_button.connect('clicked',self._on_directory_button_clicked,w)
            hbox.pack_start(w.directory_button,False,False,0)
            lb_add_hbox(lb,'ISO output directory:',hbox,w.sizegroup)
            
            adjustment = Gtk.Adjustment(float(CONFIG['mkiso.maxiso']),-1.0,10000.0,1.0,10.0,1.0)
            w.maxiso_spinbutton = Gtk.SpinButton.new(adjustment,1.0,0)
            lb_add_hbox(lb,'Maximum ISO files to keep:',w.maxiso_spinbutton,w.sizegroup)
            
            w.add(lb)
            return w
            
        def do_save(self,dialog):
            s = dialog.settings_mkiso
            CONFIG['mkiso.directory'] = s.directory_entry.get_text()
            CONFIG['mkiso.maxiso'] = s.maxiso_spinbutton.get_value_as_int()
            
    class MkisoPlugin(Plugin):
        def __init__(self):
            Plugin.__init__(self,'mkiso',
                            settings=MkisoSettings())
    
