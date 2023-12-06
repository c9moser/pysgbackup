from sgbackup.plugin import Plugin

from .settings import PLUGIN_ID,get_config_options,OPTIONS
from .commands import COMMANDS
from .checksum import create_checksums

import os

class ChecksumPlugin(Plugin):
    _archivers_backup_slot="_plugin_checksums_backup_slot"
    _archivers_delete_backup_slot="_plugin_checksums_delete_backup_slot"

    def __init__(self,app):
        Plugin.__init__(self,app,PLUGIN_ID,"Checksum Plugin","Creating and checking checksum files.")
        self.__commands=[]

    def __on_archivers_backup(self,manager,archiver,game,filename):
        create_checksums(self.application,game,filename)
    
    def __on_archivers_delete_backup(self,manager,game,filename):
        config = self.application.config
        for csum in config.get_string_list(PLUGIN_ID,'checksums'):
            csum_file = '.'.join((filename,csum))
            if os.path.isfile(csum_file):
                os.unlink(csum_file)
                if config.verbose:
                    print("[DELETE] {file}".format(file=csum_file))

    def do_enable(self):
        if not self.application.config.has_section(PLUGIN_ID):
            opts = get_config_options()
        else:
            opts = OPTIONS

        for sect,sect_spec in opts.items():
            for key,spec in sect_spec.items():
                self.application.config.register_option(sect,key,**spec)

            for cmd,aliases in COMMANDS:
                command = cmd(self.application)
                self.__commands.append(command)
                if aliases:
                    self.application.commands.add(command,aliases)
                else:
                    self.application.commands.add(command)

            am = self.application.archivers
            setattr(am,self._archivers_backup_slot,am.connect('backup',self.__on_archivers_backup))
            setattr(am,self._archivers_delete_backup_slot,am.connect('delete-backup',self.__on_archivers_delete_backup))

    def do_disable(self):
        for command in self.__commands:
            self.application.commands.remove(command)
        self.__commands = []

        am = self.application.archivers
        if hasattr(am,self._archivers_backup_slot):
            am.disconnect(getattr(am,self._archivers_backup_slot))
            delattr(am,self._archivers_backup_slot)
        if hasattr(am,self._archivers_delete_backup_slot):
            am.disconnect(getattr(am,self._archivers_delete_backup_slot))
            delattr(am,self._archivers_delete_backup_slot)

PLUGIN = ChecksumPlugin