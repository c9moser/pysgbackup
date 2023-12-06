import os
from string import Template
import bz2

DEFAULT_TEMPLATE=Template("""${TITLE}

SYNOPSIS
${SYNOPSIS}
""")

def create_help_title(command):
    width = 80
    header = "SAVEGAME BACKUP UTILITY"
    header_len = len(header)

    indent = (width // 2) - (header_len // 2)

    command_title = "sgbackup {}".format(command)
    command_title_len = len(command_title)

    if command_title_len > (indent - 2):
        indent = len(command_title_len) + 2

    return "{}{}{}".format(command_title," " * (indent - command_title_len),header)

def get_default_help(command,synopsis,lang=None):
    variables = {'TITLE':create_help_title(command),'SYNOPSIS':synopsis,'COMMAND':command}
    return DEFAULT_TEMPLATE.safe_substitute(variables)

def get_builtin_help(id,command,synopsis,lang=None,variables=None):
    if variables == None:
        variables={}
    variables.update({
        'TITLE': create_help_title(command),
        'SYNOPSIS': synopsis,
        'COMMAND': command
    })

    if lang is None:
        # TODO: guess language
        lang = "C"

    if lang != "C":
        locale_file = os.path.join(
            os.path.dirname(__file__),
            '{lang}.{id}.txt'.format(lang=lang,id=id))
        locale_file_bz2 = (locale_file + '.bz2')

        if os.path.isfile(locale_file):
            with open(locale_file,'r') as txt:
                return Template(txt.read()).safe_substitute(variables)
            
        if os.path.isfile(locale_file_bz2):
            with bz2.open(locale_file_bz2,'rt') as txt:
                return Template(txt.read()).safe_substitute(variables)

    filename=os.path.join(os.path.dirname(__file__),'{id}.txt'.format(id=id))
    if os.path.isfile(filename):
        with open(filename,'r') as txt:
            return Template(txt.read()).safe_substitute(variables)
    
    filename += '.bz2'
    if os.path.isfile(filename):
        with bz2.open(filename,'rt') as txt:
            return Template(txt.read()).safe_substitute(variables)

    return DEFAULT_TEMPLATE.safe_substitute(variables)

__all__ = [
    'create_help_title'
    'get_builtin_help',
    'get_default_help'
]
