# -*- coding:utf-8 -*-
# author: Christian Moser
# file: sgbackup/plguins/ftp/__init__.py
# module: sgbackup.plugins.ftp
# license: GPL

from gi.repository import GObject
from sgbackup.plugin import Plugin
from . import commands
from .ftp import FtpManager

OPTIONS={
    'ftp': {
        'host':{'type':'string','default':'localhost'},
        'port':{'type':'integer','default':21,'validate':lambda x: (x > 0 and x < 65536)},
        'user':{'type':'string','default':'anonymous'},
        'password':{'type':'string','default':''},
        'timeout':{'type':'integer','default':300},
        'useTLS':{'type':'boolean','default':False},
        'autoBackup':{'type':'boolean','default':False},
        'test':{'type':'boolean','default':True},
    },
}

class FtpPlugin(Plugin):
    def __init__(self,app):
        Plugin.__init__(self,app,"ftp","FTP/FTPS Plugin","Plugin for syncing backups with FTP/FTPS.")
        self.__ftp = FtpManager(app)
        self.__commands = []

    @GObject.Property
    def ftp(self):
        return self.__ftp
        
    def do_enable(self):
        for group,group_spec in OPTIONS.items():
            for key,spec in group_spec.items():
                self.application.config.register_option(group,key,**spec)

        self.ftp.enable()
        for c,a in commands.COMMANDS:
            cmd = c(self.application)
            self.__commands.append(cmd)
            if a:
                self.application.commands.add(cmd,a)
            else:
                self.application.commands.add(cmd)
        

    def do_disable(self):
        self.ftp.disable()
        for c in self.__commands:
            self.application.commands.remove(c)
        self.__commands = []


PLUGIN = FtpPlugin