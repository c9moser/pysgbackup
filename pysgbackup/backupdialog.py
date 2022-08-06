import gi
from gi.repository import Gtk,GLib,Gio
import threading

import sgbackup

class BackupDialog(Gtk.Dialog):
    def __init__(self,parent=None):
        Gtk.Dialog.__init__(self,parent=parent)
        self.__games = []
        self.__cancel = False
        
        self.set_title('PySGBackup: Backup Savegames')
        
        self.progress = Gtk.ProgressBar()
        self.progress.set_show_text(True)
        self.get_content_area().pack_start(self.progress,False,False,0)
        self.button_cancel = self.add_button('Cancel',Gtk.ResponseType.CANCEL)
        self.button_close = self.add_button('Close',Gtk.ResponseType.CLOSE)
        self.show_all()
        
    @property
    def games(self):
        return self.__games
        
    def add_game(self,game):
        self.games.append(game)
        self.button_close.set_sensitive(False)
        
    
    def _backup_thread(self):
        for g in self.games:
            if self.__cancel:
                GLib.idle_add(self._on_thread_finished)
                return
                
            GLib.idle_add(self._on_thread_update,g)
            sgbackup.backup.backup(g)
            
        GLib.idle_add(self._on_thread_update,None)
        GLib.idle_add(self._on_thread_finished)
            
    def _on_thread_update(self,game):
        cnt = len(self.games)
        if game:
            for i in range(len(self.games)):
                if self.games[i].game_id == game.game_id:
                    cnt = i
                    
        if game:
            self.progress.set_text('Backing up "{}"'.format(game.name))
        else:
            self.progress.set_text('Done')
            
        fraction = cnt/len(self.games)
        self.progress.set_fraction(cnt/len(self.games))
        self.progress.show()
        
    def _on_thread_finished(self):
        self.button_close.set_sensitive(True)
    
    def do_response(self,response):
        if response == Gtk.ResponseType.CANCEL:
            self.__cancel = True
        elif response == Gtk.ResponseType.CLOSE:
            self.hide()
            self.destroy()

    def run(self):
        thread = threading.Thread(target=self._backup_thread)
        thread.daemon = True
        thread.start()
        return Gtk.Dialog.run(self)
        
class FinalBackupDialog(Gtk.Dialog):
    def __init__(self,parent=None):
        Gtk.Dialog.__init__(self,parent)
        self.__game = None
        self.__undo_final = undo_final
    
    @property
    def game(self):
        return self.__game
        
    @game.setter
    def game(self,game):
        if isinstance(game,str):
            self.game = sgbackup.db.get_game(game)
        if isinstance(game,sgbackup.games.Game):
            self.__game = game
        else:
            raise TypeError('"game" needs to be an "sgbackup.games.Game" instance or a valid GameID!')
            
        
        
    def _backup_thread(self):
        if self.game:
            self.game.final_backup = True
            sgbackup.backup.backup(game)
        GLib.idle_add(self._on_thread_finished)
        
    def _on_thread_finished(self):
        #self.button_close.set_sensitive(True)
        #if pysgbackup.app.appwindow:
            #pysgbackup.app.appwindow.update_gameview()
            #pysgbackup.app.appwindow.update_backupview()
            
    def do_response(self,response):
        if response == Gtk.ResponseType.CLOSE:
            self.hide()
            self.destroy()
        
    def run(self):
        thread = threading.Thread(target=self.backup_thread())
        thread.dameon = True
        thread.start()
        self.run()
        
