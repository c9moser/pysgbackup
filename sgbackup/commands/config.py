# -*- coding: utf-8 -*-

# Author: Christian Moser
# License: GPL
# File: sgbackup/commands/config.py
# Module: sgbackup.commands.config

from ..command import CommandOptions,Command
from ..help import get_builtin_help
from ..error import OptionError

class ConfigOptions(CommandOptions):
    ID = "config"
    MODES = ['list','get','set']
    def __init__(self, app,cmd):
        CommandOptions.__init__(self,app,self.ID,cmd)
        self.__mode = 'list'
        self.__option = None
        self.__value = None

    @property
    def mode(self):
        return self.__mode
    @mode.setter
    def mode(self,m:str):
        if not m in self.MODES:
            raise ValueError("Not a valid mode!")
        self.__mode = m

    @property
    def option(self):
        return self.__option
    @option.setter
    def option(self,o:str):
        errfmt="Option \"{option}\" is invalid! ({reason})"
        if not '.' in o:
            raise ValueError(errfmt.format(option=o,reason="Illegal option format!"))
        
        section,key=o.split('.',1)
        if not section in self.application.config.configuration:
            reason = "Section \"{section}\" is not registered!".format(section=section)
            raise ValueError(errfmt.format(option=o,reason=reason))
        
        if not key in self.application.config.configuration[section]:
            reason = "Option Key \"{key}\" does not exist in section \"{section}\"!".format(key=key,section=section)
            raise ValueError(errfmt.format(option=o,reason=reason))
        
        self.__option = o

    @property
    def section(self):
        if self.option and '.' in self.option:
            return self.option.split('.',1)[0]
        return None
    @property
    def key(self):
        if self.option and '.' in self.option:
            return self.option.split('.',1)[1]
        return None
    
    @property
    def value(self):
        return self.__value
    @value.setter
    def value(self,v):
        def str_to_bool(s):
            if s.lower() in ("1","y","yes","true","on"):
                return True
            elif s.lower() in ("0","n","no","false","off"):
                return False
            else:
                raise TypeError("Value is not a boolean value!")

        if self.option is None:
            self.__value = v
            return
        
        try:
            type=self.application.config.configuration[self.section][self.key]['type']
        except Exception as error:
            type='string'


        if type in ('bool','boolean'):
            if isinstance(v,str):
                value = str_to_bool(v)
            else:
                try:
                    value = bool(v)
                except:
                    raise TypeError("Value can not converted to a boolean value!")
        elif type in ("bool-list","boolean-list"):
            value=[]
            if isinstance(v,list) or isinstance(v,tuple):
                for i in v:
                    if isinstance(i,str):
                        value.append(str_to_bool(i))
                    else:
                        try:
                            value.append(bool(i))
                        except:
                            raise TypeError("Value can not converted to a boolean value!")
            elif isinstance(v,str):
                for i in v.split(';'):
                    value.append(str_to_bool(i))
            else:
                raise TypeError("Illegal value type!")
        elif type in ('int','integer'):
            try:
                if 'base' in self.application.config.configuration[self.section][self.key]:
                    value = int(v,base=self.application.config.configuration[self.section][self.key]['base'])
                else:
                    value = int(v)
            except:
                raise TypeError("Value is not an integer!")
        elif type in ('int-list','integer-list'):
            value=[]
            if isinstance(v,list) or isinstance(v,tuple):
                for i in v:
                    try:
                        if 'base' in self.application.config.configuration[self.section][self.key]:
                            value.append(int(v,base=self.application.config.configuration[self.section][self.key]['base']))
                        else:
                            value.append(int(i))
                    except:
                        raise TypeError("Value is not an integer list!")
            elif isinstance(v,str):
                for i in v.split(';'):
                    try:
                        if 'base' in self.application.config.configuration[self.section][self.key]:
                            value.append(int(v,base=self.application.config.configuration[self.section][self.key]['base']))
                        else:
                            value.append(int(i))
                    except:
                        raise TypeError("Value is not an integer list!")
            else:
                raise TypeError("Illegal value type!")
        elif type == 'float':
            try:
                value = float(v)
            except:
                raise TypeError("Illegal value type!")
        elif type == 'float-list':
            value = []
            if isinstance(v,list) or isinstance(v,tuple):
                for i in v:
                    try:
                        value.append(float(i))
                    except:
                        raise TypeError("Value is not a float list!")
            elif isinstance(v,str):
                for i in v.split(';'):
                    try:
                        value.append(float(i))
                    except:
                        raise TypeError("Value is not a float list!")
            else:
                raise TypeError("Illegal value type!")
        elif type in ('str','string'):
            try:
                value=str(v)
            except:
                raise TypeError("Value is not a string!")
        elif type in ('str-list','string-list'):
            value = []
            if isinstance(v,str):
                for i in v.split(';'):
                    value.append(i)
            elif isinstance(v,list) or isinstance(v,tuple):
                for i in v:
                    try:
                        value.append(str(i))
                    except:
                        raise TypeError("Value is not a string list!")
            
            else:
                raise TypeError("Value is not a string list!")
        else:
            value = v

        if 'validate' in self.application.config.configuration[self.section][self.key]:
            if not self.application.config.configuration[self.section][self.key]['validate'](value):
                raise ValueError("Validation of value failed!")
        self.__value = value
    
    @property
    def is_valid(self):
        if ((self.mode == "list")
                or (self.mode == "get" and self.option)
                or (self.mode == "set" and self.option and self.value is not None)):
            return True
        return False

class Config(Command):
    ID = ConfigOptions.ID

    def __init__(self,app):
        Command.__init__(self,app,self.ID,"Manage configuration.")

    def get_synopsis(self, command=None):
        return """sgbackup {command} [list]
sgbackup {command} get OPTION
sgbackup {command} set OPTION VALUE""".format(command=command)

    def get_help(self,command=None):
        if command is None:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)

    def do_parse(self, cmd, argv):
        options = ConfigOptions(self.application,cmd)

        if len(argv) == 0:
            return options
        
        if argv[0] in ConfigOptions.MODES:
            options.mode = argv[0]
        else:
            raise OptionError("Unknown mode \"{mode}\" for command \"{command}\"!".format(mode=argv[0]),command=cmd)
        
        if options.mode == "get":
            if len(argv) < 2:
                raise OptionError("Too few arguments for command \"{command}\" mode \"get\"!".format(command=cmd))
            elif len(argv) > 2:
                raise OptionError("Too many arguments for command \"{command}\" mode \"get\"!".format(command=cmd))
            try:
                options.option = argv[1]
            except Exception as err:
                raise OptionError("Illegal option \"{option}\"! ({reason})".format(option=argv[1],reason=err))
        if options.mode == "set":
            if len(argv) < 3:
                raise OptionError("Too few arguments for command \"{command}\" mode \"set\"!".format(command=cmd))
            if len(argv) > 3:
                raise OptionError("Too many arguments for command \"{command}\" mode \"set\"!".format(command=cmd))
            
            try:
                options.option = argv[1]
            except Exception as err:
                raise OptionError("Illegal option \"{option}\"! ({reason})".format(option=argv[1],reason=err))
            
            try:
                options.value = argv[2]
            except Exception as err:
                raise OptionError("Unable to set value for option \"{option}\"! ({reason})".format(option=argv[1],reason=err))
            
        return options
    
    def do_execute(self, options=ConfigOptions):
        def get_boolean_string(b):
            if b:
                return "true"
            return "false"

        if not options.is_valid:
            raise RuntimeError("Invalid config options!")
        
        CONFIG_TYPES=[
            'bool',
            'boolean',
            'bool-list',
            'boolean-list',
            'int',
            'integer',
            'int-list',
            'integer-list',
            'float',
            'float-list',
            'str',
            'string',
            'str-list',
            'string-list'
        ]
        cfg = self.application.config
        configuration = cfg.configuration

        if options.mode == "list":    
            for section in sorted(configuration.keys()):
                for opt in sorted(configuration[section].keys()):
                    if ('type' in configuration[section][opt] and configuration[section][opt]['type'] in CONFIG_TYPES):
                        config_type = configuration[section][opt]['type']
                    else:
                        config_type = "string"

                    if config_type in ('bool','boolean'):
                        value = get_boolean_string(cfg.get_boolean(section,opt))

                    elif config_type in ('bool-list','boolean-list'):
                        blist = cfg.get_boolean_list(section,opt)
                        if blist is None:
                            value=""
                        else:
                            value = ";".join((get_boolean_string(i) for i in blist))
                    elif config_type in ('int','integer'):
                        iv = cfg.get_integer(section,opt)
                        if iv is None:
                            value=""
                        else:
                            if 'base' in configuration[section][opt]:
                                base = configuration[section][opt]['base']
                                if base == 8:
                                    value = oct(iv)
                                elif base == 16:
                                    value = hex(iv)
                                else:
                                    value = str(iv)
                            else:
                                value=str(iv)
                    elif config_type in ('int-list','integer-list'):
                        ilist = cfg.get_integer_list(section,opt)
                        if ilist is None:
                            value=""
                        elif 'base' in configuration[section][opt]:
                            base = configuration[section][opt]['base']
                            if base == 8:
                                    value = ";".join((oct(i) for i in ilist))
                            elif base == 16:
                                    value = ";".join((hex(i) for i in ilist))
                            else:
                                value = ";".join((str(i) for i in ilist))
                        else:
                            value=";".join((str(i) for i in ilist))
                    elif config_type == 'float':
                        f = cfg.get_float(section,opt)
                        if f is None:
                            value = ""
                        else:
                            value = str(f)
                    elif config_type == 'float-list':
                        flist = cfg.get_float_list(section,opt)
                        if flist is None:
                            value = ""
                        else:
                            value = ";".join((str(i) for i in flist))
                    elif config_type in  ("str","string"):
                        s = cfg.get_string(section,opt)
                        if s is None:
                            value = ""
                        else:
                            value = "\"{}\"".format(s)
                    elif config_type in ('str-list','string-list'):
                        slist = cfg.get_string_list(section,opt)
                        if slist is None:
                            value = ""
                        else:
                            value=";".join(("\"{}\"".format(i) for i in slist))

                    print("{section}.{option}={value}".format(section=section,option=opt,value=value))
            return 0
        elif options.mode == 'get':
            config_type='string'
            if ('type' in configuration[options.section][options.key]
                    and configuration[options.section][options.key]['type'] in CONFIG_TYPES):
                config_type = configuration[options.section][options.key]['type']
            
            if config_type in ('bool','boolean'):
                print(get_boolean_string(cfg.get_boolean(options.section,options.key)))
            elif config_type in ('bool-list','boolean-list'):
                blist = cfg.get_boolean_list(options.section,options.key)
                if blist is None:
                    print("")
                else:
                    print(";".join((get_boolean_string(i) for i in blist)))
            elif config_type in ('int','integer'):
                iv = cfg.get_integer(options.section,options.key)
                if iv is None:
                    print("")
                else:
                    print(str(iv))
            elif config_type in ('int-list','integer-list'):
                ilist = cfg.get_integer_list(options.section,options.key)
                if ilist is None:
                    print("")
                else:
                    print(";".join((str(i) for i in ilist)))
            elif config_type == 'float':
                f = cfg.get_float(options.section,options.key)
                if f is None:
                    print("")
                else:
                    print(str(f))
            elif config_type == 'float-list':
                flist = cfg.get_float_list(options.section,options.key)
                if f is None:
                    print("")
                else:
                    print(";".join((str(i) for i in flist)))
            elif config_type in ('str','string'):
                s = cfg.get_string(options.section,options.key)
                if s is None:
                    print("")
                else:
                    print("\"{}\"".format(s))
            elif config_type in ('str-list','string-list'):
                slist = cfg.get_string_list(options.section,options.key)
                if slist is None:
                    print("")
                else:
                    print(";".join(("\"{}\"".format(i) for i in slist)))
            else:
                s = cfg.get_string(options.section,options.key)
                if s is None:
                    print("")
                else:
                    print("\"{}\"".format(str(s)))
            return 0
        elif options.mode == 'set':
            config_type = 'string'
            ok=False
            if ('type' in configuration[options.section][options.key]
                    and configuration[options.section][options.key]['type'] in CONFIG_TYPES):
                config_type = configuration[options.section][options.key]['type']

            if config_type in ('bool','boolean'):
                cfg.set_boolean(options.section,options.key,options.value)
                if cfg.verbose:
                    print("{option} => {value}".format(option=options.option,value=get_boolean_string(options.value)))
                ok = True
            elif config_type in ('bool-list','boolean-list'):
                cfg.set_boolean_list(options.section,options.key,options.value)
                if cfg.verbose:
                    print("{option} => {value}".format(option=options.option,value=";".join((get_boolean_string(i) for i in options.value))))
                ok = True
            elif config_type in ('int','integer'):
                cfg.set_integer(options.section,options.key,options.value)
                if cfg.verbose:
                    print("{option} => {value}".format(option=options.option,value=str(options.value)))
                ok = True
            elif config_type in ('int-list','integer-list'):
                cfg.set_integer_list(options.section,options.key,options.value)
                if cfg.verbose:
                    print("{option} => {value}".format(option=options.option,value=";".join((str(i) for i in options.value))))
                ok = True
            elif config_type == 'float':
                cfg.set_float(options.section,options.key,options.value)
                if cfg.verbose:
                    print("{option} => {value}".format(option=options.options,value=str(options.value)))
                ok = True
            elif config_type == 'float-list':
                cfg.set_float_list(options.section,options.key,options.value)
                if cfg.verbose:
                    print("{option} => {value}".format(option=options.option,value=";".join((str(i) for i in options.value))))
                ok = True
            elif config_type in ('str','string'):
                cfg.set_string(options.section,options.key,str(options.value))
                if cfg.verbose:
                    print("{option} => \"{value}\"".format(option=options.option,value=str(options.value)))
                ok = True
            elif config_type in ('str-list','string-list'):
                cfg.set_string_list(options.section,options.key,options.value)
                if cfg.verbose:
                    print("{option} => {value}".format(option=options.option,value=";".join(("\"{}\"".format(i) for i in options.value))))
                ok = True

            if ok:
                cfg.save()

            return 0
        return 1
    
COMMANDS=[
    (Config,None),
]
