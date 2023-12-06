# -*- coding:utf-8 -*-
# author: Christian Moser
# file: sgbackup/error.py
# module: sgbackup.error
# license: GPL

class OptionError(Exception):
    def __init__(self,message="",*args):
        Exception.__init__(self,message,*args)

    @property
    def message(self):
        return self.args[0]

class CommandError(Exception):
    def __init__(self,message="",*args):
        Exception.__init__(self,message,*args)

    @property
    def message(self):
        return self.args[0]
    

class GameConfError(Exception):
    def __init__(self,message,*args):
        Exception.__init__(self,message,*args)

    @property
    def message(self):
        return self.args[0]
