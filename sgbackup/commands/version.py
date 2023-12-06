# -*- coding: utf-8 -*-

from ..command import Command,CommandOptions_None as VersionOptions
from ..error import OptionError 
from ..config.settings import VERSION

class Version(Command):
    def __init__(self,app):
        Command.__init__(self,app,'version','Print version information.')

    def do_parse(self, cmd, argv):
        if (len(argv) > 0):
            raise OptionError("\"sgbackup version\" doeas not take any arguments!")
        return VersionOptions(self.application,cmd)
    
    def do_execute(self, options:VersionOptions):
        print("sgbackup-{version}".format(version=VERSION))
        return 0
    
COMMANDS=[
    (Version,None),
]
