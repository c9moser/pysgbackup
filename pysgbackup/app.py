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

import os
import gi
from gi.repository import Gtk,Gio,GLib,Gdk

from . import appwindow

import sgbackup

class Application(Gtk.Application):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.__appwindow = None
        Gdk.threads_init()
        
        
    @property
    def appwindow(self):
        return self.__appwindow
        
    def __create_actions(self):
        def add_simple_action(name,callback):
            action = Gio.SimpleAction.new(name,None)
            action.connect('activate',callback)
            self.add_action(action)
            return action
        
        add_simple_action('quit',self._on_action_quit)
        add_simple_action('about',self._on_action_about)
        
        
    def _on_action_quit(self,action,data):
        if self.appwindow:
            self.appwindow.hide()
            self.appwindow.destroy()
        self.__appwindow = None    
        self.quit()
            
    def _on_action_about(self,action,data):
        def on_response(dialog,response):
            dialog.destroy()
            
        dialog = Gtk.AboutDialog()
        dialog.set_title('About PySGBackup')
        dialog.set_name('PySGBackup')
        dialog.set_program_name('pysgbackup')
        dialog.set_version('.'.join((str(i) for i in sgbackup.config.CONFIG['version'])))
        dialog.set_authors(['Christian Moser'])
        dialog.set_license_type(Gtk.License.GPL_3_0)
        dialog.connect('response',on_response)
        
        dialog.run()
            
    
    def do_activate(self):
        self.__create_actions()
        
        #if not self.appwindow:
        self.__appwindow = appwindow.AppWindow(application=self)
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(os.path.dirname(__file__),'menu.ui'))
        menu = builder.get_object('appmenu')
        
        self.set_app_menu(menu)
        self.appwindow.present()
        
