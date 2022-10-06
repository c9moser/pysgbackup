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

import sgbackup

if 'mkiso' in sgbackup.plugins.PLUGINS:
    from pysgbackup.plugins import Settings,Plugin
    from gi.repository import Gtk,GObject
    import os
    import threading
    import string
    
    class MkisoSettings(Settings):
        def __init__(self):
            Settings.__init__(self,'mkiso','Create ISO-Files',
                              attribute = 'mkiso_settings')
                              
        def do_create_widget(self,dialog):
            def on_enable_switch_toggled(switch,state,w):
                db = sgbackup.database.Database()
                if switch.get_active():
                    db.enable_plugin('mkiso')
                    w.directory_label.set_sensitive(True)
                    w.directory_entry.set_sensitive(True)
                    w.directory_button.set_sensitive(True)
                    w.maxiso_label.set_sensitive(True)
                    w.maxiso_spinbutton.set_sensitive(True)
                else:
                    db.disable_plugin('mkiso')
                    w.directory_label.set_sensitive(False)
                    w.directory_entry.set_text(sgbackup.config.CONFIG['mkiso.directory.template'])
                    w.directory_entry.set_sensitive(False)
                    w.directory_button.set_sensitive(False)
                    w.maxiso_label.set_sensitive(False)
                    w.maxiso_spinbutton.set_value(float(sgbackup.config.CONFIG['mkiso.maxiso']))
                    w.maxiso_spinbutton.set_sensitive(False)
                db.close()
            # on_enable_switch_toggled()
                
            def on_directory_button_clicked(button,w):
                directory = string.Template(w.directory_entry.get_text()).safe_substitute(sgbackup.config.get_template_vars())
                dialog = Gtk.FileChooserDialog("PySGBackup: ISO output directory",
                                               w.get_toplevel(),
                                               Gtk.FileChooserAction.SELECT_FOLDER)
                dialog.add_button('Accept',Gtk.ResponseType.ACCEPT)
                dialog.add_button('Cancel',Gtk.ResponseType.CANCEL)
                dialog.set_create_folders(True)
                dialog.set_current_folder(directory)
                result = dialog.run()
                dialog.hide()
                if result == Gtk.ResponseType.ACCEPT:
                    w.directory_entry.set_text(dialog.get_filename())
            # on_directory_button_clicked()
            
            w = Gtk.ScrolledWindow()
            lb = Gtk.ListBox()
            w.sizegroup = Gtk.SizeGroup()
            w.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
            
            hbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
            label = Gtk.Label('Enable plugin:')
            w.sizegroup.add_widget(label)
            hbox.pack_start(label,False,False,5)
            w.enable_switch = Gtk.Switch()
            hbox.pack_end(w.enable_switch,False,False,5)
            lb_row = Gtk.ListBoxRow()
            lb_row.add(hbox)
            lb.add(lb_row)

            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            w.directory_label = Gtk.Label('Output directory:')
            w.sizegroup.add_widget(w.directory_label)
            hbox.pack_start(w.directory_label,False,False,5)
            w.directory_entry = Gtk.Entry()
            w.directory_entry.set_text(sgbackup.config.CONFIG['mkiso.directory.template'])
            hbox.pack_start(w.directory_entry,True,True,5)
            w.directory_button = Gtk.Button.new_from_icon_name('document-open',Gtk.IconSize.BUTTON)
            w.directory_button.connect('clicked',on_directory_button_clicked,w)
            hbox.pack_start(w.directory_button,False,False,5)
            lb_row = Gtk.ListBoxRow()
            lb_row.add(hbox)
            lb.add(lb_row)
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            w.maxiso_label = Gtk.Label('Maximum ISO-files:')
            w.sizegroup.add_widget(w.maxiso_label)
            hbox.pack_start(w.maxiso_label,False,False,5)
            adjustment = Gtk.Adjustment(float(sgbackup.config.CONFIG['mkiso.maxiso']),0.0,10000.0,1.0,10.0,1.0)
            w.maxiso_spinbutton = Gtk.SpinButton.new(adjustment,1.0,0)
            hbox.pack_start(w.maxiso_spinbutton,True,True,5)
            lb_row = Gtk.ListBoxRow()
            lb_row.add(hbox)
            lb.add(lb_row)
            
            w.enable_switch.connect('notify::active',on_enable_switch_toggled,w)
            w.enable_switch.set_active(sgbackup.plugins.PLUGINS['mkiso'].enabled)
            
            w.add(lb)
            return w
        # MkisoSettings.do_create_widget()
        
        def do_save(self,parent):
            w = parent.mkiso_settings
            if w.enable_switch.get_active():
                t = w.directory_entry.get_text()
                sgbackup.config.CONFIG['mkiso.directory.template'] = t
                sgbackup.config.CONFIG['mkiso.directory'] = string.Template(t).safe_substitute(sgbackup.config.get_template_vars())
                
                sgbackup.config.CONFIG['mkiso.maxiso'] = w.maxiso_spinbutton.get_value_as_int()
        # MkisoSettings.do_save()
    # Settings class
    
    class MkisoPlugin(Plugin):
        def __init__(self):
            Plugin.__init__(self,'mkiso','Create ISO-files',
                            settings=MkisoSettings(),
                            sgbackup_plugin = sgbackup.plugins.PLUGINS['mkiso'],
                            sgbackup_plugin_enable = True)
                            
            def do_enable(self,appwindow):
                Plugin.do_enable(self,appwindow)
                
            def do_disable(self,appwindow):
                Plugin.do_disable(self,appwindow)
    # MkisoPlugin class
    
    plugin = MkisoPlugin()
