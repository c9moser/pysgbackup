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
    from gi.repository import Gio,Gtk,GObject,GLib,Gdk,GdkPixbuf
    import os,sys
    import subprocess
    import threading
    import pysgbackup
    from pysgbackup import plugins
    import sgbackup
    from sgbackup.plugins import checksum


    PLUGIN_ID = 'checksum'
    MENU_FILE = os.path.join(os.path.dirname(__file__),'menu.ui')
    
    class ChecksumSettings(plugins.Settings):
        def __init__(self):
            plugins.Settings.__init__(self,PLUGIN_ID,'Checksum Settings',
                                      attribute='checksum_settings')
    
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
            
            def on_plugin_switch_notify_changed(switch,state,widget):
                if switch.get_active() and not widget.enable_switch.get_active():
                    widget.enable_switch.set_active(True)
                elif not switch.get_active() and widget.enable_switch.get_active():
                    widget.enable_switch.set_active(False)
            # on_plugin_switch_notify_changed()
            
            def on_enable_switch_changed(switch,state,dialog,widget):
                active = switch.get_active()
                engine = 'pysgbackup'
                pid = "{}:{}".format(engine,PLUGIN_ID)
            
                if pid in dialog.settings_plugins.plugin_switches:
                    switch = dialog.settings_plugins.plugin_switches[pid]
                else:
                    switch = None
                    
                if active:
                    if switch and not switch.get_active():
                        switch.set_active(True)
                    widget.algorithm_label.set_sensitive(True)
                    widget.algorithm_combobox.set_sensitive(True)
                    widget.bsdtags_label.set_sensitive(True)
                    widget.bsdtags_switch.set_sensitive(True)
                    widget.check_label.set_sensitive(True)
                    widget.check_switch.set_sensitive(True)
                else:
                    if switch and switch.get_active():
                        switch.set_active(False)
                    widget.algorithm_label.set_sensitive(False)
                    widget.algorithm_combobox.set_active_id(sgbackup.config.CONFIG['checksum.algorithm'])
                    widget.algorithm_combobox.set_sensitive(False)
                    widget.bsdtags_label.set_sensitive(False)
                    widget.bsdtags_switch.set_active(sgbackup.config.CONFIG['checksum.bsd-tags'])
                    widget.bsdtags_switch.set_sensitive(False)
                    widget.check_label.set_sensitive(False)
                    widget.check_switch.set_active(sgbackup.config.CONFIG['checksum.check'])
                    widget.check_switch.set_sensitive(False)
            # on_enable_switch_changed()
            
            w = Gtk.ScrolledWindow()
            w.sizegroup = Gtk.SizeGroup()
            w.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
            
            lb = Gtk.ListBox()
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            label = create_label("Enable Plugin:",w.sizegroup)
            hbox.pack_start(label,False,False,5)
            w.enable_switch = Gtk.Switch()
            w.enable_switch.connect('notify::active',on_enable_switch_changed,dialog,w)
            hbox.pack_end(w.enable_switch,False,False,5)
            listbox_add_widget(lb,hbox)
            
            
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
            
            w.enable_switch.set_active(plugins.PLUGINS[PLUGIN_ID].enabled)
            
            try:
                switch = dialog.settings_plugins.plugin_switches["pysgbackup:checksum"]
                switch.connect('notify::active',on_plugin_switch_notify_changed,w)
            except Exception as error:
                print(error,file=sys.stderr)
            w.add(lb)
            return w
        # ChecksumSettings.do_create_widget()
        
        def do_save(self,dialog):
            w = dialog.checksum_settings
            
            if w.enable_switch.get_active():
                sgbackup.config.CONFIG['checksum.algorithm'] = w.algorithm_combobox.get_active_id()
                sgbackup.config.CONFIG['checksum.bsd-tags'] = w.bsdtags_switch.get_active()
                sgbackup.config.CONFIG['checksum.check'] = w.check_switch.get_active()
        # ChecksumSettings.do_save()
    # ChecksumSettings class
    
    class ChecksumCreateDialog(Gtk.Dialog):
        def __init__(self,parent,games=None):
            def create_label(text,sizegroup):
                l = Gtk.Label(text)
                l.set_xalign(0.0)
                sizegroup.add_widget(l)
                return l
            # create_label()
            
            Gtk.Dialog.__init__(self,parent)
            self.set_title('Creating missing Checksums')
            
            self.__abort = False
            self.__games = self.__init_games(games)
            
            self.sizegroup = Gtk.SizeGroup()
            self.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
            
            vbox = self.get_content_area()
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.check_label = create_label('Check internal checksums:',self.sizegroup)
            hbox.pack_start(self.check_label,False,False,5)
            self.check_switch = Gtk.Switch()
            self.check_switch.set_active(sgbackup.config.CONFIG['checksum.check'])
            hbox.pack_end(self.check_switch,False,False,5)
            vbox.pack_start(hbox,False,False,0)
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.bsdtags_label = create_label('Enable BSD-Tags:',self.sizegroup)
            hbox.pack_start(self.bsdtags_label,False,False,5)
            self.bsdtags_switch = Gtk.Switch()
            self.bsdtags_switch.set_active(sgbackup.config.CONFIG['checksum.bsd-tags'])
            hbox.pack_end(self.bsdtags_switch,False,False,5)
            vbox.pack_start(hbox,False,False,0)
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.force_label = create_label('Force the creation of checksum files:',self.sizegroup)
            hbox.pack_start(self.force_label,False,False,5)
            self.force_switch = Gtk.Switch()
            self.force_switch.set_active(False)
            hbox.pack_end(self.force_switch,False,False,5)
            vbox.pack_start(hbox,False,False,0)
            
            vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
            
            self.progress = Gtk.ProgressBar()
            self.progress.set_show_text(True)
            self.progress.set_fraction(0.0)
            vbox.pack_start(self.progress,False,False,0)
            
            vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
            
            buttonbox = self.get_action_area()
            self.run_button = Gtk.Button('Run')
            self.run_button.connect('clicked',self._on_run_button_clicked)
            buttonbox.pack_start(self.run_button,False,False,0)
            buttonbox.set_child_secondary(self.run_button,True)
            
            self.abort_button = Gtk.Button('Abort')
            self.abort_button.connect('clicked',self._on_abort_button_clicked)
            self.abort_button.set_sensitive(False)
            buttonbox.pack_start(self.abort_button,False,False,0)
            buttonbox.set_child_secondary(self.abort_button,True)
            
            self.close_button = self.add_button('Close',Gtk.ResponseType.CLOSE)
            self.show_all()
            
        def __init_games(self,games):
            game_list=[]
            db = sgbackup.database.Database()
            if not games:
                for i in db.list_game_ids():
                    g = db.get_game(i)
                    if g:
                        game_list.append({'game':g})
            else:
                for i in games:
                    b=[]
                    if isinstance(i,str):
                        g = db.get_game(i)
                        if not g:
                            game_list.append({'game':g})
                    elif isinstance(i,sgbackup.games.Game):
                        game_list.append({'game':g})
                    elif isinstance(i,dict):
                        if 'game' in i:
                            game_spec = {}
                            if isinstance(i['game'],sgbackup.games.Game):
                                game_spec['game'] = i['game']
                            elif isinstance(i['game'],str):
                                g = db.get_game(i['game'])
                                if g:
                                    game_spec['game'] = g
                            
                            if 'game' in game_spec:
                                if 'backups' in i:
                                    game_spec['backups'] = i['backups']
                                    
                                game_list.append(game_spec)
            db.close()            
            return game_list
        # ChecksumCreateDialog.__init_games()
                    
        def has_checksum_file(self,backup):
            algorithm = sgbackup.config.CONFIG['checksum.algorithm']
            if algorithm == 'None':
                return True
                
            fn = '.'.join((backup,algorithm))
            ckfiles = checksum.find_checksum_files(backup)
            if fn in ckfiles:
                return True
            return False
        # ChecksumCreateDialog.has_checksum_file()
            
        @GObject.Property
        def games(self):
            return self.__games
            
        @GObject.Property
        def bsdtags(self):
            return self.bsdtags_switch.get_active()
        @bsdtags.setter
        def bsdtags(self,b):
            self.bsdtags_switch.set_active(bool(b))
            
        @GObject.Property
        def check(self):
            return self.check_switch.get_active()
        @check.setter
        def check(self,b):
            self.check_switch.set_active(bool(b))
            
        @GObject.Property
        def force(self):
            return self.force_switch.get_active()
        @force.setter
        def force(self,b):
            self.force_switch.set_active(bool(b))

        
        def _on_run_button_clicked(self,button):
            self.__abort = False
            self.check_label.set_sensitive(False)
            self.check_switch.set_sensitive(False)
            self.bsdtags_label.set_sensitive(False)
            self.bsdtags_switch.set_sensitive(False)
            self.force_label.set_sensitive(False)
            self.force_switch.set_sensitive(False)
            self.run_button.set_sensitive(False)
            self.close_button.set_sensitive(False)
            self.abort_button.set_sensitive(True)
            
            thread = threading.Thread(target=self._thread_func,daemon=True)
            thread.start()
        # ChecksumCreateDialog._on_run_button_clicked()
            
        def _on_abort_button_clicked(self,button):
            self.__abort = True
        # ChecksumCreateDialog._on_abort_button_clicked()
            
        def _on_update(self,text,fraction):
            self.progress.set_text(text)
            self.progress.set_fraction(fraction)
        # ChecksumCreateDialog._on_update()
            
        def _on_thread_finished(self):
            self.check_label.set_sensitive(True)
            self.check_switch.set_sensitive(True)
            self.bsdtags_label.set_sensitive(True)
            self.bsdtags_switch.set_sensitive(True)
            self.force_label.set_sensitive(True)
            self.force_switch.set_sensitive(True)
            self.close_button.set_sensitive(True)
            self.run_button.set_sensitive(True)
            self.abort_button.set_sensitive(False)
            
        def _thread_func(self):
            algorithm =  sgbackup.config.CONFIG['checksum.algorithm']
            if algorithm == 'None':
                text = 'Nothing to do ...'
                GLib.idle_add(self._on_update,text,1.0)
                GLib.idle_add(self._on_thread_finished)
                return
                
            fraction = lambda steps,cnt: (cnt/steps)
            
            GLib.idle_add(self._on_update,"Creating file list ...",0.0)
            
            db = sgbackup.database.Database()
            
            count = 0
            backup_list = []
            for i in self.games:
                g = i['game']
                if 'backups' in i:
                    for b in i['backups']:
                        backup_list.append((g,b))
                else:
                    for backup in sgbackup.backup.find_backups(g):
                        if self.force or not self.has_checksum_file(backup):
                            backup_list.append((g,backup))
            
            if self.check:
                n_steps = len(backup_list * 2) + 1
            else:
                n_steps = len(backup_list) + 1
                
            for game,backup in backup_list:
                if self.__abort:
                    GLib.idle_add(self._on_thread_finished)
                    return
                
                if self.check:
                    count += 1
                    text = 'Checking {} ...'.format(os.path.basename(backup))
                    GLib.idle_add(self._on_update,text,fraction(n_steps,count))
                    if not sgbackup.backup.check_backup(db,game,backup):
                        print('Checking backup {} failed!'.format(backup),file=sys.stderr)
                        count += 1
                        continue
                        
                count += 1
                cksum_file = '.'.join((backup,algorithm))
                text = "Creating checksum {} ...".format(os.path.basename(cksum_file))
                GLib.idle_add(self._on_update,text,fraction(n_steps,count))
                
                # creating checksum
                args = [checksum.CHECKSUM[algorithm]]
                if self.bsdtags:
                    args.append('--tag')
                args.append(os.path.basename(backup))
                
                cwd = os.getcwd()
                os.chdir(os.path.dirname(backup))
                proc = subprocess.run(args,capture_output=True)
                if proc.returncode == 0:
                    try:
                        with open(cksum_file,'wb') as ofile:
                            ofile.write(proc.stdout)
                        db_backup = db.get_game_backup(game,backup)
                        extrafile_found = False
                        cksum_basename = os.path.basename(cksum_file)
                        for ef in db_backup['extrafiles']:
                            if cksum_basename == ef['filename']:
                                extrafile_found = True
                        if not extrafile_found:
                            db.add_game_backup_extrafile(game,backup,cksum_file,True)
                    except Exception as error:
                        print("Unable to create checksum-file! ({})".format(error))
                else:
                    print("Unable to create checksum! ({})".format(proc.stderr))
                
            db.close()
            GLib.idle_add(self._on_update,'Done',1.0)
            GLib.idle_add(self._on_thread_finished)
        # ChecksumCreateDialog._thread_func()
    # ChecksumCreateDialog class       

    class ChecksumCheckDialog(Gtk.Dialog):
        (
            GV_COL_GAMEID,
            GV_COL_GAME,
            GV_COL_FILENAME,
            GV_COL_TEXT,
            GV_COL_PIXBUF
        ) = range(5)
        
        def __init__(self,parent,games=None):  
            def create_label(text,sizegroup):
                l = Gtk.Label(text)
                l.set_xalign(0.0)
                if sizegroup:
                    sizegroup.add_widget(l)
                return l
            # create_label()
            
            Gtk.Dialog.__init__(self,parent)
            self.set_title('Check Checksum Files')
            self.set_default_size(600,400)
            self.__games = self.__init_games(games)
            self.__abort = False
            self.sizegroup = Gtk.SizeGroup()
            self.sizegroup.set_mode(Gtk.SizeGroupMode.HORIZONTAL)
            
            vbox = self.get_content_area()
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.failed_label = create_label('Delete files where check failed:',self.sizegroup)
            hbox.pack_start(self.failed_label,False,False,5)
            self.failed_switch = Gtk.Switch()
            self.failed_switch.set_active(True)
            hbox.pack_end(self.failed_switch,False,False,5)
            vbox.pack_start(hbox,False,False,0)
            
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            self.check_label = create_label('Perform internal check:',self.sizegroup)
            hbox.pack_start(self.check_label,False,False,5)
            self.check_switch = Gtk.Switch()
            self.check_switch.set_active(True)
            hbox.pack_end(self.check_switch,False,False,5)
            vbox.pack_start(hbox,False,False,0)
            
            vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
            
            self.progress = Gtk.ProgressBar()
            self.progress.set_show_text(True)
            vbox.pack_start(self.progress,False,False,0)
            
            vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
            
            # BEGIN: Add progressbook
            self.progressbook = Gtk.Notebook()
            
            ## Add Games-TreeView to progressbook
            scrolled = Gtk.ScrolledWindow()
            model = Gtk.TreeStore(str,str,str,str,GdkPixbuf.Pixbuf)
            self.progress_gameview = Gtk.TreeView.new_with_model(model)

            renderer = Gtk.CellRendererPixbuf()
            column = Gtk.TreeViewColumn("Icon",renderer,pixbuf=self.GV_COL_PIXBUF)
            self.progress_gameview.append_column(column)
            
            renderer = Gtk.CellRendererText()
            self.progress_gameview.column_text = Gtk.TreeViewColumn("Icon",renderer,text=self.GV_COL_TEXT)
            self.progress_gameview.append_column(self.progress_gameview.column_text)
            
            scrolled.add(self.progress_gameview)
            self.progressbook.append_page(scrolled,Gtk.Label('Games'))
            
            ## Add outputview to progressbook
            scrolled = Gtk.ScrolledWindow()
            self.progress_outputview = Gtk.TextView()
            self.progress_outputview.set_editable(False)
            buffer = self.progress_outputview.get_buffer()
            self.progress_outputview_error_tag = buffer.create_tag('error',foreground='red')
            
            scrolled.add(self.progress_outputview)
            self.progressbook.append_page(scrolled,Gtk.Label('Output'))
            
            # add progressbook to vbox
            self.progressbook.set_current_page(0)
            vbox.pack_start(self.progressbook,True,True,0)
            # END: add progressbook
            
            vbox.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL),False,False,5)
            
            buttonbox = self.get_action_area()
            self.run_button = Gtk.Button('Run')
            self.run_button.connect('clicked',self._on_run_button_clicked)
            buttonbox.pack_start(self.run_button,False,False,0)
            buttonbox.set_child_secondary(self.run_button,True)
            
            self.abort_button = Gtk.Button('Abort')
            self.abort_button.connect('clicked',self._on_abort_button_clicked)
            self.abort_button.set_sensitive(False)
            buttonbox.pack_start(self.abort_button,False,False,0)
            buttonbox.set_child_secondary(self.abort_button,True)
            
            self.close_button = self.add_button('Close',Gtk.ResponseType.CLOSE)
            
            self.show_all()
        # ChecksumCheckDialog.__init__()
                
        def __init_games(self,games):
            db = sgbackup.database.Database()
                
            game_list=[]
                
            if not games:
                for i in db.list_game_ids():
                    g = db.get_game(i)
                    if g:
                        game_list.append({'game':g})
            else:
                for i in games:
                    if isinstance(i,str):
                        g = db.get_game(i)
                        if g:
                            game_list.append({'game':g})
                    elif isinstance(i,sgbackup.games.Game):
                        game_list.append({'game':i})
                    elif isinstance(i,dict):
                        if 'game' in dict:
                            game_spec = {}
                            if isinstance(i['game'],sgbackup.games.Game):
                                game_spec['game'] = i['game']
                            elif isinstance(i['game'],str):
                                g = db.get_game(i['game'])
                                if g:
                                    game_spec['game'] = g
                                
                            if 'backups' in i:
                                game_spec['backups'] = i
                                    
                            if 'game' in game_spec:
                                games.append(game_spec)
            return game_list
        # ChecksumCheckDialog.__init_games()
        
        @GObject.Property
        def games(self):
            return self.__games
            
        def get_checksum_files(self,backup):
            return checksum.find_checksum_files(backup)
            
        def get_pixbuf_from_icon_name(icon_name):
            theme = Gtk.IconTheme.get_default()
            pixbuf = theme.load_icon(icon_name,Gtk.IconSize.MENU,Gtk.IconLookupFLags.NONE)
            if not pixbuf:
                pixbuf = theme.load_icon('image-missing',Gtk.IconSize.MENU,Gtk.IconLookupFLags.NONE)
            return pixbuf
            
        def _on_run_button_clicked(self,button):
            self.failed_label.set_sensitive(False)
            self.failed_switch.set_sensitive(False)
            self.check_label.set_sensitive(False)
            self.check_switch.set_sensitive(False)
            self.run_button.set_sensitive(False)
            self.close_button.set_sensitive(False)
            self.abort_button.set_sensitive(True)
            
            self.__abort = False
            thread = threading.Thread(target=self._thread_func,daemon=True)
            thread.start()
        
        def _on_abort_button_clicked(self,button):
            self.__abort = True
            
        def _thread_func(self):
            fraction = lambda n,cnt: cnt/n
            
            def check_internal_checksum(db,game,backup):
                db_backup = db.get_game_backup(game,backup)
                h = hashlib.new(db_backup['checksum'])
                with open(b,'rb') as ifile:
                    h.update(ifile)
                if db_backup['hash'] == h.hexdigest():
                    return True
                return False
            # check_internal_checksum()
               
            db = sgbackup.database.Database()
            
            Glib.idle_add(self._on_update,'Preparing ...',0.0)
            
            check_games = {}
            for game_spec in self.games:
                g = game_spec['game']
                if 'backups' in game_spec:
                    backups = game_spec['backups']
                else:
                    backups = sgbackup.backup.find_backups(g)
                    
                if not g.game_id in check_games:
                    check_games[g.game_id] = {'game':g,'backups':backups}
                else:
                    for i in backups:
                        cg_backups = check_games[g.game_id]['backups']
                        has_backup = False
                        for j in cg_backups:
                            if i == j:
                                has_backup=True
                                break
                        if not has_backup:
                            cg_backups.append(i)
            
            n_steps = 0
            for spec in check_games.values():
                for i in spec['backups']:
                    n_steps += 1
                    
            if self.check_switch.get_active():
                n_steps *= 2
                
            n_steps += 1
            
            count = 0
            
            for gid,spec in check_games.items():
                if self.__abort:
                    GLib.idle_add(self._on_thread_finished)
                    return
                    
                for b in spec['backups']:
                    count += 1
                    text = "Checking {} ...".format(os.path.basename(b))
                    check_ok = True
                    
                    if self.check_switch.get_active():
                        GLib.idle_add(self._on_update,text,fraction(n_steps,count))
                        
                        if check_internal_checksum(db,spec['game'],b):
                            GLib.idle_add(self._on_update_outputview,
                                          '"{}" internal check [OK]\n'.format(os.path.basename(b)))
                        else:
                            GLib.idle_add(self._on_update_outputview,
                                        '"{}" internal check [FAILED]\n'.format(os.path.basename(b)),
                                        True)
                            GLib.idle_add(self._on_update_gameview,spec['game'],b,True)
                            
                            if self.failed_switch.get_active():
                                sgbackup.backup.delete_backup(db,spec['game'],b)
                                
                            continue

                    GLib.idle_add(self._on_update,text,fraction(n_steps,count))
                    checksum_files = checksum.find_checksum_files(b)
                    checksum_ok = True
                    cwd = os.getcwd()
                    os.chdir(os.path.dirname(b))
                    for ckf in checksum_files:
                        f,ext = os.path.splitext(ckf)
                        if ext in checksum.CHECKSUM:
                            program = checksum.CHECKSUM[ext]
                            args = [program,'--check',os.path.basename(ckf)]
                            fmt = '{0}: {1} [{2}]'
                            proc = subprocess.run(args)
                            if proc.returncode == 0:
                                text = fmt.format(ext,os.path.basename(b),'OK')
                                GLib.idle_add(self._on_update_outputview,text)
                            else:
                                checksum_ok = False
                                text = fmt.format(ext,os.path.basename(b),'FAILED')
                                GLib.idle_add(self._on_update_outputview,text,True)
                                
                    if checksum_ok:
                        GLib.idle_add(self._on_update_gameview,spec['game'],b)
                    else:
                        GLib.idle_add(self._on_update_gameview,spec['game'],b,True)
                        if self.failed_switch.get_active():
                            sgbackup.backup.delete_backup(db,game,b)
            # Done checking checksums
            
            GLib.idle_add(self._on_update,'Done',1.0)
            GLib.idle_add(self._on_thread_finished)
        # ChecksumCheckDialog._thread_func()
            
        def _on_thread_finished(self):
            self.failed_label.set_sensitive(True)
            self.failed_switch.set_sensitive(True)
            self.check_label.set_sensitive(True)
            self.check_switch.set_sensitive(True)
            self.run_button.set_sensitive(True)
            self.abort_button.set_sensitive(False)
            self.close_button.set_sensitive(True)
        # ChecksumCheckDialog._on_thread_finished()
            
        def _on_update_outputview(self,text,is_error=False):
            buffer = self.progress_outputview.get_buffer()
            if is_error:
                buffer.insert_with_tags(buffer.get_end_iter(),
                                        text,
                                        self.progress_outputview_error_tag)
            else:
                buffer.insert(buffer.get_end_iter(),text)
            
            #self.progress_outputview.show()
                
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
            iter = buffer.get_iter_at_line(buffer.get_line_count())
            self.progressview.scroll_to(iter)
            self.progress_outputview.show()
        # ChecksumCheckDialog._on_update_outputview()
        
        def _on_update_gameview(self,game,file,is_error=False):
            model = self.progress_gameview.get_model()
            if not hasattr(game,'gameview_iter'):
                game.gameview_iter = model.append(None,(game.game_id,
                                                        game.name,
                                                        None,
                                                        game.name,
                                                        self.get_pixbuf_from_icon_name('applications-games-symbolic')))
            if is_error:
                model.set_value(game.gameview_iter,self.GV_COL_PIXBUF,self.get_pixbuf_from_icon_name('dialog-error'))
                pixbuf = self.get_pixbuf_from_icon_name('gtk-no')
            else:
                pixbuf = self.get_pixbuf_from_icon_name('gtk-yes')
            
            iter = model.append(game.gameview_iter,(game.game_id,game.name,os.path.file,os.path.basename(file),pixbuf))
            
            while Gtk.events_pending():
                Gtk.main_iteration_do(False)
                
            self.progress_gameview.scroll_to_cell(model.get_path(iter),self.progress_gameview.column_text)
            self.progress_gameview.show()            
        # ChecksumCheckDialog._on_update_gameview()
            
        def _on_update(self,text,fraction):
            self.progress.set_text(text)
            self.progress.set_fraction(fraction)
            self.progress.show()
        # ChecksumCheckDialog._on_update()
    # ChecksumCheckDialog class
    
    class ChecksumPlugin(plugins.Plugin):
        def __init__(self):
            plugins.Plugin.__init__(self,PLUGIN_ID,'Checksum Plugin',
                                    version=sgbackup.config.version(),
                                    description='Creating checksum files for backups.',
                                    settings=ChecksumSettings(),
                                    sgbackup_plugin='checksum',
                                    sgbackup_plugin_enable=True,                                             
                                    menu={'file':MENU_FILE,'object':'checksum-menu'},
                                    gameview_menu={'file':MENU_FILE,'object':'checksum-gameview-menu'},
                                    backupview_menu={'file':MENU_FILE,'object':'checksum-backupview-menu'})
        # ChecksumPlugin.__init__()

        def has_checksum_file(self,backup_filename):
            algorithm = sgbackup.config.CONFIG['checksum.algorithm']
            if algorithm == 'None':
                return True
                
            return os.path.isfile('.'.join((backup_filename,algorithm)))
        # ChecksumPlugin.has_checksum_file()
        
        def get_checksum_files(self,backup_filename):
            return checksum.find_checksum_files(backup_filename)
        # ChecksumPlugin.get_checksum_files()
            
        def _on_action_check_all(self,action,data,appwindow):
            dialog = ChecksumCheckDialog(appwindow)
            dialog.run()
            dialog.hide()
            dialog.destroy()
        # ChecksumPlugin._on_action_check_all()
            
        def _on_action_check_game(self,action,data,appwindow):
            model,iter = appwindow.gameview.get_selection().get_selected()
            if iter:
                gid = model.get_value(iter,appwindow.GV_COL_GAMEID)
                dialog = ChecksumCheckDialog(appwindow,games=[gid])
                dialog.run()
                dialog.hide()
                dialog.destroy()
        # ChecksumPlugin._on_action_check_game()
            
        def _on_action_check_backup(self,action,data,appwindow):
            gv_model,gv_iter = appwindow.gameview.get_selection().get_selected()
            bv_model,bv_iter = appwindow.backupview.get_selection().get_selected()
            
            if gv_iter and bv_iter:
                gid = gv_model.get_value(gv_iter,appwindow.GV_COL_GAMEID)
                backup = bv_model.get_value(bv_iter,appwindow.BV_COL_FILENAME)
                dialog = ChecksumCheckDialog(appwindow,games=[{'game':gid,'backups':[backup]}])
                dialog.run()
                dialog.hide()
                dialog.destroy()
        # ChecksumPlugin._on_action_check_backup()
        
        def _on_action_create_all(self,action,data,appwindow):
            dialog = ChecksumCreateDialog(self)
            dialog.run()
            dialog.hide()
            dialog.destroy()
        # ChecksumPlugin._on_action_create_all()
            
        def _on_action_create_game(self,action,data,appwindow):
            model,iter = appwindow.gameview.get_selection().get_selected()
            if iter:
                game_id = model.get_value(iter,appwindow.GV_COL_GAMEID)
                dialog = ChecksumCreateDialog(self,games=[{'game':game_id}])
                dialog.run()
                dialog.hide()
                dialog.destroy()
        # ChecksumPlugin._on_action_create_game()
                            
        def _on_action_create_backup(self,action,data,appwindow):
            gv_model,gv_iter = appwindow.gameview.get_selection().get_selected()
            bv_model,bv_iter = appwindow.backupview.get_selection().get_selected()
            
            if gv_iter and bv_iter:
                game_id = gv_model.get_value(gv_iter,appwindow.GV_COL_GAMEID)
                backup = bv_model.get_value(bv_iter,appwindow.BV_COL_FILENAME)
                dialog = ChecksumCreateDialog(self,games=[{'game':game_id,'backups':[backup]}])
                dialog.run()
                dialog.hide()
                dialog.destroy()
        # ChecksumPlugin._on_action_create_backup()
            
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
                appwindow.action_checksum_create_backup.connect('activate',self._on_action_create_backup,appwindow)
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

