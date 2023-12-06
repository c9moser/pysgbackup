# -*- coding:utf-8 -*-
# author: Christian Moser
# file: sgbackup/__init__.py
# module: sgbackup
# license: GPL

import gi
gi.require_version('GObject','2.0')
gi.require_version('GLib','2.0')

import sys

from . import error
from .commandmanager import CommandManager
from .command import (
    Command,
    CommandOptions,
    CommandOptions_None
)

from . import config
from .application import Application
from .archiver._archivermanager import ArchiverManager
from .archiver._archiver import ArchiverBase
from . import archiver

SGBACKUP_VERSION_MAJOR=config.VERSION_MAJOR
SGBACKUP_VERSION_MINOR=config.VERSION_MINOR
SGBACKUP_VERSION_MICRO=config.VERSION_MICRO
SGBACKUP_VERSION_NUMBER=config.VERSION_NUMBER
SGBACKUP_VERSION=config.VERSION

Config = config.Config

def main():
    """
    This is the main function called by the `sgbackup` program.
    It just executes :func:`sgbackup.application.Application.run`
    and exits afterwards.
    """
    app = Application()
    return app.run(sys.argv[1:])

sgbackup_main = main

__all__=[
    "SGBACKUP_VERSION_MAJOR",
    "SGBACKUP_VERSION_MINOR",
    "SGBACKUP_VERSION_MICRO",
    "SGBACKUP_VERSION_EXTENSION",
    "SGBACKUP_VERSION_NUMBER",
    "SGBACKUP_VERSION",
    "error",
    "Application",
    "archiver",
    "ArchiverBase",
    "ArchiverManager",
    "Command",
    "CommandOptions",
    "CommandOptions_None",
    "CommandManager",
    "Config",
    "sgbackup_main"
]
