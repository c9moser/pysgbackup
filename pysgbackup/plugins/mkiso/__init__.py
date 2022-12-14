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
PLUGIN_ID = 'mkiso'

if PLUGIN_ID in sgbackup.plugins.PLUGINS:
    import pysgbackup
    from pysgbackup.plugins import Settings,Plugin,PLUGINS
    from gi.repository import Gtk,GObject,Gio,GLib
    import os,sys
    import threading
    import string
    import subprocess
    
    class MkisoSettings(Settings):
        def __init__(self):
            Settings.__init__(self,PLUGIN_ID,'Create ISO Settings',
                              attribute = 'mkiso_settings')
                              
        def do_create_widget(self,dialog):
            def create_label(text,sizegroup=None):
                l = Gtk.Label(text)
                l.set_xalign(0.0)
                if sizegroup:
                    sizegroup.add_widget(l)
                return l
            # create_label()
            
            def on_enable_switch_toggled(switch,state,dialog,w):
                plugin_switch = None
                pid = "{}:{}".format("pysgbackup",PLUGIN_ID)
                if pid in dialog.settings_plugins.plugin_switches:
                    plugin_switch = dialog.settings_plugins.plugin_switches[pid]
                    
                if switch.get_active():
                    if plugin_switch and not plugin_switch.get_active():
                        plugin_switch.set_active(True)
                    w.finals_label.set_sensitive(True)
                    w.finals_switch.set_sensitive(True)
                    w.directory_label.set_sensitive(True)
                    w.directory_entry.set_sensitive(True)
                    w.directory_button.set_sensitive(True)
                    w.maxiso_label.set_sensitive(True)
                    w.maxiso_spinbutton.set_sensitive(True)
                else:
                    if plugin_switch and plugin_switch.get_active():
                        plugin_switch.set_active(False)
                        
                    w.finals_label.set_sensitive(False)
                    w.finals_switch.set_active(sgbackup.config.CONFIG['mkiso.all-finals'])
                    w.finals_switch.set_sensitive(False)
                    w.directory_label.set_sensitive(False)
                    w.directory_entry.set_text(sgbackup.config.CONFIG['mkiso.directory.template'])
                    w.directory_entry.set_sensitive(False)
                    w.directory_button.set_sensitive(False)
                    w.maxiso_label.set_sensitive(False)
                    w.maxiso_spinbutton.set_value(float(sgbackup.config.CONFIG['mkiso.maxiso']))
                    w.maxiso_spinbutton.set_sensitive(False)
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
            
            def on_plugin_switch_notify_active(switch,state,widget):
                if switch.get_active() != widget.enable_switch.get_active():
                    widget.enable_switch.set_active(switch.get_active())
            # def on_plugin_switch_notify_active()
            
            w = Gtk.ScrolledWindow()
            lb = Gtk.ListBox()
            w.sizegroup = Gtk.SizeGroup()
            w.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
            
            hbox = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL)
            label = create_label('Enable plugin:',w.sizegroup)
            hbox.pack_start(label,False,False,5)
            w.enable_switch = Gtk.Switch()
            hbox.pack_end(w.enable_switch,False,False,5)
            lb_row = Gtk.ListBoxRow()
            lb_row.add(hbox)
            lb.add(lb_row)

            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            w.finals_label = create_label('Include all final backups:',w.sizegroup)
            hbox.pack_start(w.finals_label,False,False,5)
            w.finals_switch = Gtk.Switch()
            w.finals_switch.set_active(sgbackup.config.CONFIG['mkiso.all-finals'])
            hbox.pack_end(w.finals_switch,False,False,5)
            lb_row = Gtk.ListBoxRow()
            lb_row.add(hbox)
            lb.add(lb_row)
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            w.directory_label = create_label('Output directory:',w.sizegroup)
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
            w.maxiso_label = create_label('Maximum ISO-files:',w.sizegroup)
            hbox.pack_start(w.maxiso_label,False,False,5)
            adjustment = Gtk.Adjustment(float(sgbackup.config.CONFIG['mkiso.maxiso']),0.0,10000.0,1.0,10.0,1.0)
            w.maxiso_spinbutton = Gtk.SpinButton.new(adjustment,1.0,0)
            hbox.pack_start(w.maxiso_spinbutton,True,True,5)
            lb_row = Gtk.ListBoxRow()
            lb_row.add(hbox)
            lb.add(lb_row)
            
            w.enable_switch.connect('notify::active',on_enable_switch_toggled,dialog,w)
            w.enable_switch.set_active(sgbackup.plugins.PLUGINS['mkiso'].enabled)
            
            pid = "{}:{}".format('pysgbackup',PLUGIN_ID)
            if pid in dialog.settings_plugins.plugin_switches:
                plugin_switch = dialog.settings_plugins.plugin_switches[pid]
                plugin_switch.connect('notify::active',on_plugin_switch_notify_active,w)
                
            w.add(lb)
            return w
        # MkisoSettings.do_create_widget()
        
        def do_save(self,parent):
            w = parent.mkiso_settings
            if w.enable_switch.get_active():
                sgbackup.config.CONFIG['mkiso.all-finals'] = w.finals_switch.get_active()
                t = w.directory_entry.get_text()
                sgbackup.config.CONFIG['mkiso.directory.template'] = t
                sgbackup.config.CONFIG['mkiso.directory'] = string.Template(t).safe_substitute(sgbackup.config.get_template_vars())
                
                sgbackup.config.CONFIG['mkiso.maxiso'] = w.maxiso_spinbutton.get_value_as_int()
        # MkisoSettings.do_save()
    # Settings class
    
    class MkisoDialog(Gtk.Dialog):
        def __init__(self,parent):
            def create_label(text,sizegroup):
                l = Gtk.Label(text)
                l.set_xalign(0.0),
                sizegroup.add_widget(l)
                return l
                
            Gtk.Dialog.__init__(self,parent)
            self.set_title('PySGBackup: Create ISO File')
            
            buttonbox = self.get_action_area()
            self.create_button = Gtk.Button('Create ISO')
            self.create_button.connect('clicked',self._on_create_button_clicked)
            buttonbox.pack_start(self.create_button,False,False,0)
            buttonbox.set_child_secondary(self.create_button,True)
            self.close_button = self.add_button('Close',Gtk.ResponseType.CLOSE)
            
            self.sizegroup = Gtk.SizeGroup()
            self.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
            
            vbox = self.get_content_area()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.finals_label = create_label('Include all finals:',self.sizegroup)
            hbox.pack_start(self.finals_label,False,False,5)
            self.finals_switch = Gtk.Switch()
            self.finals_switch.set_active(sgbackup.config.CONFIG['mkiso.all-finals'])
            hbox.pack_end(self.finals_switch,False,False,5)
            vbox.pack_start(hbox,False,False,0)
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.output_label = create_label('Enable user ISO file:',self.sizegroup)
            hbox.pack_start(self.output_label,False,False,5)
            self.output_switch = Gtk.Switch()
            self.output_switch.connect('notify::active',self._on_output_switch_toggled)
            hbox.pack_end(self.output_switch,False,False,5)
            vbox.pack_start(hbox,False,False,0)
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.outfile_label = create_label('Output file:',self.sizegroup)
            hbox.pack_start(self.outfile_label,False,False,5)
            self.outfile_entry = Gtk.Entry()
            hbox.pack_start(self.outfile_entry,True,True,5)
            self.outfile_button = Gtk.Button.new_from_icon_name('document-open',Gtk.IconSize.BUTTON)
            self.outfile_button.connect('clicked',self._on_outfile_button_clicked)
            hbox.pack_start(self.outfile_button,False,False,5)
            vbox.pack_start(hbox,False,False,0)
            
            vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
            
            self.progress = Gtk.ProgressBar()
            self.progress.set_pulse_step(0.01)
            vbox.pack_start(self.progress,False,False,0)
            
            vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
            
            self._on_output_switch_toggled(self.output_switch,None)
            self.show_all()
        # MkisoDialog.__init__()
            
        def _on_outfile_button_clicked(self,button):
            filter = Gtk.FileFilter()
            filter.add_pattern('*.iso')
            dialog = Gtk.FileChooserDialog('Select ISO file',
                                           self,
                                           Gtk.FileChooserAction.SAVE)
            dialog.set_create_folders(True)
            dialog.set_do_overwrite_confirmation(True)
            if not self.outfile_entry.get_text():
                dialog.set_current_folder(GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS))
            else:
                dialog.set_current_folder(os.path.dirname(self.outfile_entry.get_text()))

            dialog.add_button('Accept',Gtk.ResponseType.ACCEPT)
            dialog.add_button('Cancel',Gtk.ResponseType.CANCEL)
            dialog.set_filter(filter)
            result = dialog.run()
            dialog.hide()
            if result == Gtk.ResponseType.ACCEPT:
                self.outfile_entry.set_text(dialog.get_filename())
                
            dialog.destroy()                
        #MkisoDialog._on_outfile_button_clicked()
            
        def _on_output_switch_toggled(self,switch,state):
            if switch.get_active():
                self.outfile_label.set_sensitive(True)
                self.outfile_entry.set_sensitive(True)
                self.outfile_button.set_sensitive(True)
            else:
                self.outfile_label.set_sensitive(False)
                self.outfile_button.set_sensitive(False)
                self.outfile_entry.set_sensitive(False)
        # MkisoDialog._on_output_switch_toggled()
            
        def _on_error(self,error):
            self.__thread_finished = True
            self.progress.set_fraction(0.5)

            dialog = Gtk.MessageDialog(self,
                                       Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                       Gtk.MessageType.ERROR,
                                       Gtk.ButtonsType.CLOSE,
                                       'Creating ISO file failed!')
            dialog.format_secondary_markup(error.stderr)
            dialog.run()
            dialog.hide()
            dialog.destroy()
            
        def _thread_func(self):
            if self.finals_switch.get_active():
                finals = '-a'
            else:
                finals = '-A'
                
            args = [sys.executable,'-m','sgbackup','mkiso',finals]
            if self.output_switch.get_active() and self.outfile_entry.get_text():
                args += ['-o',self.outfile_entry.get_text()]
            try:
                proc = subprocess.run(args,check=True,capture_output=True)
            except subprocess.CalledProcessError as error:
                GLib.idle_add(self._on_error,error)
                return
            
            GLib.idle_add(self._on_thread_finished)
            
        def _on_timeout(self):
            if self.__thread_finished:
                return False
                
            self.progress.pulse()
            return True
            
        def _on_thread_finished(self):
            self.__thread_finished = True
            self.progress.set_fraction(1.0)
            self.close_button.set_sensitive(True)
            
        def _on_create_button_clicked(self,button):
            self.__thread_finished = False
            self.finals_label.set_sensitive(False)
            self.finals_switch.set_sensitive(False)
            self.create_button.set_sensitive(False)
            self.close_button.set_sensitive(False)
            self.output_label.set_sensitive(False)
            self.output_switch.set_sensitive(False)
            self.outfile_button.set_sensitive(False)
            self.outfile_entry.set_sensitive(False)
            self.outfile_label.set_sensitive(False)
            
            thread = threading.Thread(target=self._thread_func,daemon=True)
            thread.start()
            GLib.timeout_add(1000//50,self._on_timeout)
    # MkisoDialog class
    
    class MkisoPlugin(Plugin):
        def __init__(self):
            Plugin.__init__(self,PLUGIN_ID,'Create ISO files',
                            version=sgbackup.config.version(),
                            settings=MkisoSettings(),
                            menu={
                                'file':os.path.join(os.path.dirname(__file__),'menu.ui'),
                                'object':'mkiso-menu'
                            },
                            sgbackup_plugin = sgbackup.plugins.PLUGINS['mkiso'],
                            sgbackup_plugin_enable = True)
               
        def _on_action_create_iso(self,action,data,appwindow):
            dialog = MkisoDialog(appwindow)
            dialog.run()
            dialog.hide()
            dialog.destroy()
            
        def do_enable(self,appwindow):
            if not hasattr(appwindow,'action_mkiso_create_iso'):
                action = Gio.SimpleAction.new('mkiso-create-iso')
                action.connect('activate',self._on_action_create_iso,appwindow)
                appwindow.add_action(action)
                appwindow.action_mkiso_create_iso = action
            else:
                appwindow.action_mkiso_create_iso.set_enabled(True)
                
            Plugin.do_enable(self,appwindow)
        # MkisoPlugin.do_enable()
        
        def do_disable(self,appwindow):
            if hasattr(appwindow,'action_mkiso_create_iso'):
                appwindow.action_mkiso_create_iso.set_enabled(False)
                
            Plugin.do_disable(self,appwindow)
        # MkisoPlugin.do_disable()
    # MkisoPlugin class
    
    plugin = MkisoPlugin()
