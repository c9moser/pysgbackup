# -*- coding:utf-8 -*-
# author: Christian Moser
# file: sgbackup/config/config.py
# module: sgbackup.config.config
# license: GPL


import os
from . import settings
import sys
from gi.repository import GObject,GLib

class Config(GObject.GObject):
    """
    This class contains the pysgbackup configuration. You should not
    create this class yourself, instead use the instance provided
    by the :class:`sgbackup.application.Application`.

    Signals
    _______
    * `load-config` - Called when an external configuration file is loaded.
    * `destroy` - Called when the instance of the class is being destroyed.
    * `save` - Called when the configuration is saved to a file.

    Members
    _______
    """
    __name__ = "sgbackup-config"
    __gsignals__ = {
        'load-config': (GObject.SIGNAL_RUN_FIRST,None,()),
        'destroy': (GObject.SIGNAL_RUN_LAST,None,()),
        'save': (GObject.SIGNAL_RUN_LAST,None,())
    }
    
    def __init__(self):
        GObject.GObject.__init__(self)
        self.__app = None
        self.__keyfile = GLib.KeyFile.new()
        self.__configuration = {}

    def _real_initialize(self,app):
        def validate_pager(pager):
            if os.path.isabs(pager):
                return os.path.isfile(pager)


            if settings.PLATFORM_WIN32:
                if pager("more.com"):
                    return True
                path_separator=';'
            else:
                path_separator=':'

            for i in os.environ['PATH'].split(path_separator):
                if os.path.isfile(os.path.join(i,pager)):
                    return True
            return False
        
        self.__app = app
        self.__init_directories()
        self.__configuration.update({
            'sgbackup': {
                'verbose': {
                    'type': 'boolean',
                    'default': False                        
                },
                'archiver' : {
                    'type': 'string',
                    'default': 'zipfile',
                    'validate': lambda x: self.application.archivers.has_archiver(x)
                },
                'backupVersions': {
                    'type': 'integer',
                    'default': 0,
                    'validate': lambda x: (int(x) >= 0)
                },
                'backupDirectory': {
                    'type': 'string',
                    'default': os.path.join(self.user_home_dir,"SaveGameBackups"),
                    'validate': lambda x: os.path.isabs(x)
                },
                'processMax': {
                    'type': 'integer',
                    'default': os.cpu_count(),
                    'validate': lambda x: (x >= 1)
                },
                'pager': {
                    'type': 'string',
                    'default': settings.get_default_pager(),
                    'validate': validate_pager
                },
                'plugins': {
                    'type': 'string-list',
                    'default': [],
                },
                'configPermission': {
                    'type': 'integer',
                    'default': 0O600,
                    'base':8,
                }
            },
            'zipfileArchiver': {
                'compression': {
                    'type': 'string',
                    'default': 'deflated',
                    'validate': lambda x: x in ('store','deflated','lzma','bzip2')
                },
                'compressLevel': {
                    'type': 'integer',
                    'default': 9,
                    'validate': lambda x: ((x >= 0) and (x <= 9))
                }
            },
            'commandGame': {
                'addGameInteractive': {
                    'type': 'boolean',
                    'default': True
                },
                'editGameInteractive': {
                    'type': 'boolean',
                    'default': True
                },
                'removeGameBackup': {
                    'type': 'boolean',
                    'default': True
                },
                'finishBackup': {
                    'type': 'boolean',
                    'default': True
                },
            },
        })

        if os.path.isfile(self.user_config):
            self.keyfile.load_from_file(self.user_config,0)
            
        self.__init_keyfile_builtin_defaults()

    def __init_directories(self):
        if not os.path.isdir(self.user_config_dir):
            os.makedirs(self.user_config_dir)

        if not os.path.isdir(self.gameconf_dir):
            os.makedirs(self.gameconf_dir)

        if not os.path.isdir(self.archiver_dir):
            os.makedirs(self.archiver_dir)

    def __init_keyfile_builtin_defaults(self):
        for sname in self.configuration.keys():
            sect = self.configuration[sname]
            for k,v in sect.items():
                if self.has_option(sname,k):
                    continue

                if 'type' in v:                    
                    if v['type'] in ('bool','boolean'):
                        if 'default' in v:
                            self.set_boolean(sname,k,v['default'])
                        else:
                            self.set_boolean(sname,k,False)
                    elif v['type'] in ('bool-list','boolean-list'):
                        if 'default' in v:
                            self.set_boolean_list(sname,k,v['default'])
                        else:
                            self.set_boolean_list(sname,k,[False])
                    elif v['type'] in ('int','integer'):
                        if 'default' in v:
                            self.set_integer(sname,k,v['default'])
                        else:
                            self.set_integer(sname,k,0)
                    elif v['type'] in ('int-list','integer-list'):
                        if 'default' in v:
                            self.set_integer_list(sname,k,v['default'])
                        else:
                            self.set_integer_list(sname,k,[0])
                    elif v['type'] == 'float':
                        if 'default' in v:
                            self.set_float(sname,k,v['default'])
                        else:
                            self.set_default(sname,k,0.0)
                    elif v['type'] == 'float-list':
                        if 'default' in v:
                            self.set_float_list(sname,k,v['default'])
                        else:
                            self.set_float_list(sname,k,[0.0])
                    elif v['type'] in ('str','string'):
                        if 'default' in v:
                            self.set_string(sname,k,v['default'])
                        else:
                            self.set_string(sname,k,"")
                    elif v['type'] in ('str-list','string-list'):
                        if 'default' in v:
                            self.set_string_list(sname,k,v['default'])
                        else:
                            self.set_string_list(sname,k,[""])
                    else:
                        raise ValueError("Unknown configuration value-type \"{type}\"!",type=v['type'])
                else:
                    try:
                        if 'default' in v:
                            self.set_string(sname,k,str(v['default']))
                        else:
                            self.set_string(sname,k,"")
                    except:
                        pass

   
    @GObject.Property(bool)
    def platform_win32(self):
        """
        (`bool`)

        `True` when the palform running sgbackup is Windows, `False` otherwise.
        
        *read only*
        """
        return settings.PLATFORM_WIN32
    
    @GObject.Property(bool)
    def is_win32(self):
        """
        (`bool`)

        `True` when the platform sgbackup is Windows, `False` otherwise. This is an alias for
        `Config.platform_win32`.

        *read only*
        """
        return settings.PLATFORM_WIN32
    
    @GObject.Property
    def keyfile(self):
        """
        (`GLib.KeyFile`)

        The `GLib.KeyFile` instance holding the configuration.

        *read only*
        """
        return self.__keyfile
    
    @GObject.Property
    def is_initialized(self):
        """
        (`bool`)

        `True` if the class is initialzed, `False` otherwise.

        *read only*
        """
        return (self.__app is not None)
    
    @GObject.Property
    def application(self):
        """
        (:class:`sgbackup.application.Application`)

        The :class:`sgbackup.application.Application` instance the configuration belongs to.

        *read only*
        """
        return self.__app
    
    @GObject.Property(str)
    def version(self):
        """
        (`str`)

        Version string of *pysgbackup*.
        
        *read only*
        """
        return settings.VERSION
    
    @GObject.Property(int)
    def version_major(self):
        """
        (`int`)

        Major version number of *pysgbackup*.

        *read only*
        """
        return settings.VERSION_MAJOR
    
    @GObject.Property(int)
    def version_minor(self):
        """
        (`int`)

        Minor version number of *pysgbackup*.

        *read only*
        """
        return settings.VERSION_MINOR
    
    @GObject.Property(int)
    def version_micro(self):
        """ 
        (`int`)

        Micro version number (Patch Level) of *pysgbackup*.

        *read only*
        """
        return settings.VERSION_MICRO

    @GObject.Property(tuple)
    def version_number(self):
        """(`tuple`)

        Version Number as a  (MAJOR,MINOR,MICRO) tuple.

        *read only*
        """
        return settings.VERSION_NUMBER
    
    
    @GObject.Property(str)
    def config_file(self):
        """
        (`str`)

        The filename of the configuration file. This is a
        full path. This is an alias for `Config.user_config`.

        *read only*
        """
        return self.user_config
    
    @GObject.Property(str)
    def user_home_dir(self):
        """
        (`str`)

        The home directory of the user running *pysgbackup*.

        *read only*
        """
        return settings.USER_HOME_DIR
    
    @GObject.Property(str)
    def user_data_dir(self):
        """
        (`str`)

        The user's data directory.

        *read only*
        """
        return settings.USER_DATA_DIR
    
    @GObject.Property(str)
    def user_config_dir(self):
        """
        (`str`)

        The user's configuration directory.

        *read only*
        """
        return settings.USER_CONFIG_DIR
    
    @GObject.Property(bool)
    def user_use_onedrive(self):
        """
        (`bool`)

        `True` if the user uses OneDrive, `False` otherwise.
        This most likely only makes sense on the Windows platform.

        *read only*
        """
        return settings.USER_USE_ONEDRIVE
    
    @GObject.Property(str)
    def user_documents_dir(self):
        """
        (`str`)

        The user's documents directory.

        *read only*
        """
        return settings.USER_DOCUMENTS_DIR
    
    @GObject.Property(str)
    def user_config(self):
        """
        (`str`)

        The full path of the configuration file.

        *read only*
        """
        if settings.PLATFORM_WIN32:
            return os.path.join(self.user_config_dir,'pysgbackup.config').replace("/","\\")
        return os.path.join(self.user_config_dir,'pysgbackup.config')
    
    
    @GObject.Property(str)
    def backup_dir(self):
        """
        (`str`)

        The directory to store the SaveGame backups in. This should be an absolute path.

        *read write*
        """
        ret = self.get_string('sgbackup','backupDirectory',self.configuration['sgbackup']['backupDirectory']['default'])
        if settings.PLATFORM_WIN32:
            return ret.replace('/','\\')
        return ret
    
    @backup_dir.setter
    def backup_dir(self,directory:str):
        if not os.path.isabs(directory):
            raise ValueError("\"backup_dir\" needs to be an absolute path!")
        return self.set_string('sgbackup','backupDirectory',directory)

    @GObject.Property(str)
    def gameconf_dir(self):
        """
        (`str`)

        The directory where the game configuration files are stored in.
        This is an absolute path.

        *read only*
        """
        if self.platform_win32:
            return os.path.join(self.user_config_dir,'games').replace('/','\\')
        return os.path.join(self.user_config_dir,'games')
        
    @GObject.Property(str)
    def archiver_dir(self):
        """
        (`str`)

        The directory where to look for CommandArchiver configuration files.
        This is an absolute path.

        *read only*
        """
        if self.platform_win32:
            return os.path.join(self.user_config_dir,'archivers').replace('/','\\')
        return os.path.join(self.user_config_dir,'archivers')
    
    @GObject.Property
    def configuration(self):
        """
        (`dict`)

        The configuration dictionary. To add configuration options use 
        the `Config.register_option()` method.

        *read only*
        """
        return self.__configuration
    
    @GObject.Property(str)
    def archiver(self):
        """
        (`str`)

        The archiver-ID of the archiver to use for backups.

        When settings a standard archiver and the ArchiverID is not registered,
        this property raises a ValueError.

        *read write*
        """
        return self.get_string('sgbackup','archiver',self.configuration['sgbackup']['archiver']['default'])
    
    @archiver.setter
    def archiver(self,id):
        if self.application.archivers.has_archiver(id):
            self.set_string('sgbackup','archiver',id)
        else:
            raise ValueError("Unknown ArchiverID \"{id}\"!".format(id=id))
        
    @GObject.Property(int)
    def backup_versions(self):
        """
        (`int`)

        The total number of backups to keep. This should be a positive integer or `0`.
        If this value is set to `0`, no backup versioning is done and all SvaeGameBackups
        are being kept, which may result in using a lot of disk-space!

        *read write*
        """
        return self.get_integer('sgbackup','backupVersions',self.configuration['sgbackup']['backupVersions']['default'])
    @backup_versions.setter
    def backup_versions(self,n):
        self.set_integer('sgbackup','backupVersions',n)

    @GObject.Property
    def verbose(self):
        """
        (`bool`)

        Enable verbose of output.

        *read write*
        """
        return self.get_boolean('sgbackup','verbose',self.configuration['sgbackup']['verbose']['default'])
    @verbose.setter
    def verbose(self,b:bool):
        self.set_boolean('sgbackup','verbose',b)
    
    @GObject.Property
    def pager(self):
        """
        (`str`)

        The pager to use for help output. On Windows this defaults to *more.com* else
        *less* is set if it exists else it is set to *more*.

        When setting a new pager and the value is not an absolute path, 
        the executable is searched in `PATH`. A `ValueError` is raised
        if the pager doeas not exist.

        *read write*
        """
        return self.get_string('sgbackup','pager',self.configuration['sgbackup']['pager']['default'])
    @pager.setter
    def pager(self,pager:str):
        if os.path.isabs(pager):
            if os.path.isfile(pager): 
                self.set_string('sgbackup','pager',pager)    
                return
            raise ValueError('\"pager\" does not exist!')
        else:
            for i in os.environ["PATH"]:
                fname = os.path.join(i,pager)
                if os.path.isfile(fname):
                    self.set_string('sgbackup','pager',fname)
                    return
                
            raise ValueError("pager \"{exec}\" does not exist in $PATH!".format(exec=pager))

    @GObject.Property
    def process_max(self):
        """
        (`int`)

        The maximum number of processes/threads to use for creating backup-archives.

        Currently only the `WinRar` CommandArchvier makes use of this option.

        * TODO: The functionality for use of this option in other archivers is to be implemented!

        *read write*
        """
        return self.get_integer('sgbackup','processMax',self.__configuration['sgbackup']['processMax']['default'])
    @process_max.setter
    def process_max(self,max:int):
        if max <= 0:
            raise ValueError('\"process_max\" needs to be a positive integer equal or greater than 0!')
        self.set_integer('sgbackup','processMax',max)

    def register_option(self,section:str,option:str,type:str,default=None,validate=None,**kwargs):
        """
        Registers a new option for configuration. A registered option can
        be set by the *config* command.

        :param section: The KeyFile section/group for the option.
        :type section: `str`
        :param option: The KeyFile option/key of the option.
        :type option: `str`
        :param type: The type of the option. Allowed values:
            * *bool* | *boolean*
            * *bool-list* | *boolean-list*
            * *int* | *integer*
            * *int-list* | *integer-list*
            * *float*
            * *float-list*
            * *str* | *string*
            * *str-list* | *string-list*
        :type type: `str`
        :param default: Default value to use.
        :type default: any
        :param validate: Validation callback. If this parameter is not None
            it should be a callable function returning `True` on success
            and `False` if validation failed. The callback takes one parameter,
            namely the value.
        :type validate: a callable or `None`
        :param kwargs: Extra values which are stored together with the option srttings
            in `Config.confugration` dictionary.
        :type kwargs: any
        """
        if not type in (
                'bool','boolean','bool-list','boolean-list',
                'int','integer','int-list','integer-list',
                'float','float-list',
                'str','string','str-list','string-list'):
            raise ValueError("Unknown Type \"{type}\"!".format(type))
        
        spec = {'type':type,'default':default}

        if callable(validate):
            spec['validate']=validate
        spec.update(kwargs)

        if not section in self.configuration:
            self.configuration[section]={option:spec}
        else:
            self.configuration[section][option]=spec

        if self.is_initialized and not self.has_option(section,option):
            if default is None:
                pass
            elif type in ('bool','boolean'):
                self.set_boolean(section,option,default)
            elif type in ('bool-list','boolean-list'):
                self.set_boolean_list(section,option,default)
            elif type in ('int','integer'):
                self.set_integer(section,option,default)
            elif type in ('int-list','integer-list'):
                self.set_integer_list(section,option,default)
            elif type == 'float':
                self.set_float(section,option,default)
            elif type == 'float-list':
                self.set_float_list(section,option,default)
            elif type in ('str','string'):
                self.set_string(section,option,default)
            elif type in ('str-list','string-list'):
                self.set_string_list(section,option,default)

    def has_section(self,section:str):
        """
        Check if the KeyFile contains a specific section/group.
        
        :param section: The section to look for.
        :type section: `str`
        :returns: `True` if the section/group exist, `False` otherwise.
        """
        return self.keyfile.has_group(section)
    
    def has_group(self,group:str):
        """
        Check if the KeyFile contains a specific section/group.

        :param group: The group to look for.
        :type group: `str`
        :returns: `True` if the section/group exist, `False` otherwise.
        """
        return self.keyfile.has_group(group)
    
    @GObject.Property
    def sections(self):
        """
        List the sections/groups of the KeyFile.

        :returns: `list(str)`
        """
        return self.keyfile.get_groups()[0]
    
    @GObject.Property
    def groups(self):
        """
        List the sections/groups of the KeyFile.

        :returns: `list(str)`
        """
        return self.keyfile.get_groups()[0]
    
    def has_option(self,section:str,key:str):
        """
        Check if an option/key exists in KeyFile.

        :param section: The section/group for the option.
        :type section: `str`
        :param key: The key/option to look for.
        :type key: `str`
        :returns: `True` if the option has been found, `False` otherwise.
        """
        if self.keyfile.has_group(section):
            cfg_keys = self.keyfile.get_keys(section)
            if (cfg_keys and key in cfg_keys[0]):
                return True
        return False
    
    def has_key(self,section:str,key:str):
        """
        Check if an option/key exists in KeyFile.

        :param section: The section/group for the option.
        :type section: `str`
        :param key: The key/option to look for.
        :type key: `str`
        :returns: `True` if the option has been found, `False` otherwise.
        """
        return self.has_option(section,key)
    
    def get(self,section:str,key:str,default=None):
        """
        Get a option from KeyFile.

        :param section: The section/group for the option.
        :type section: `str`
        :param key: The option/key for the option.
        :type key: `str`
        :param default: A default value for the option.
        :type default: any
        :returns: The value found in the KeyFile if found, else
            it returns the default value set in the parameter if it is
            not None. If both fails this function tries to return
            the default value set in `Config.configuration` if that
            fails too this function returns None
        """
        if self.has_option(section,key):
            return self.keyfile.get_value(section,key)
        
        if default is None:
            try:
                return self.configuration[section][key]['default']
            except:
                return None
        return default
    
    def get_boolean(self,section:str,key:str,default=None):
        """
        Get a boolean option from KeyFile.

        :param section: Section/group the option is in.
        :type section: `str`
        :param key: The name of the option.
        :type key: `str`
        :param default: The default value to return if the lookup fails.
        :type default: `bool` or `None`
        :returns: The option value if found in KeyFile. If the value is not
            found and `default` is not `None`, `default` is returned. If the value
            is not found and `default` is `None`, the default value of 
            `Config.configuration` is returned if set else `None` is returned.
        """
        if self.has_option(section,key):
            return self.keyfile.get_boolean(section,key)
        
        if default is None:
            try:
                return self.configuration[section][key]['default']
            except:
                return None
        return default
    
    def get_boolean_list(self,section,key,default=None):
        """
        Get a boolean list from KeyFile.

        :param section: Section/group the option is in.
        :type section: `str`
        :param key: The name of the option.
        :type key: `str`
        :param default: The default value to return if the lookup fails.
        :type default: `list(bool)` or `None`
        :returns: The option value if found in KeyFile. If the value is not
            found and `default` is not `None`, `default` is returned. If the value
            is not found and `default` is `None`, the default value of 
            `Config.configuration` is returned if set else `None` is returned.
        """
        if self.has_option(section,key):
            blist = self.keyfile.get_boolean_list(section,key)
            if blist is not None:
                ret = []
                for b in blist:
                    ret.append(b)

        if default is None:
            try:
                return self.configuration[section][key]['default']
            except:
                return None
        return default
    
    def get_integer(self,section,key,default=None):
        """
        Get an integer option from KeyFile.

        :param section: Section/group the option is in.
        :type section: `str`
        :param key: The name of the option.
        :type key: `str`
        :param default: The default value to return if the lookup fails.
        :type default: `int` or `None`
        :returns: The option value if found in KeyFile. If the value is not
            found and `default` is not `None`, `default` is returned. If the value
            is not found and `default` is `None`, the default value of 
            `Config.configuration` is returned if set else `None` is returned.
        """
        if self.has_option(section,key):
            return self.keyfile.get_int64(section,key)
        if default is None:
            try:
                return self.configuration[section][key]['default']
            except:
                return None
        return default
    
    def get_integer_list(self,section,key,default=None):
        """
        Get a integer list from KeyFile.

        :param section: Section/group the option is in.
        :type section: `str`
        :param key: The name of the option.
        :type key: `str`
        :param default: The default value to return if the lookup fails.
        :type default: `list(int)` or `None`
        :returns: The option value if found in KeyFile. If the value is not
            found and `default` is not `None`, `default` is returned. If the value
            is not found and `default` is `None`, the default value of 
            `Config.configuration` is returned if set else `None` is returned.
        """
        if self.has_option(section,key):
            ilist = self.keyfile.get_int64_list(section,key)
            if ilist is not None:
                ret = []
                for i in ilist:
                    ret.append(i)
                return ret
        if default is None:
            try:
                return self.configuration[section][key]['default']
            except:
                return None        
        return default
    
    def get_float(self,section,key,default=None):
        """
        Get a float option from KeyFile.

        :param section: Section/group the option is in.
        :type section: `str`
        :param key: The name of the option.
        :type key: `str`
        :param default: The default value to return if the lookup fails.
        :type default: `float` or `None`
        :returns: The option value if found in KeyFile. If the value is not
            found and `default` is not `None`, `default` is returned. If the value
            is not found and `default` is `None`, the default value of 
            `Config.configuration` is returned if set else `None` is returned.
        """
        if self.has_option(section,key):
            return self.keyfile.get_double(section,key)
        if default is None:
            try:
                return self.configuration[section][key]['default']
            except:
                return None
        return default
    
    def get_float_list(self,section,key,default=None):
        """
        Get a float list from KeyFile.

        :param section: Section/group the option is in.
        :type section: `str`
        :param key: The name of the option.
        :type key: `str`
        :param default: The default value to return if the lookup fails.
        :type default: `list(float)` or `None`
        :returns: The option value if found in KeyFile. If the value is not
            found and `default` is not `None`, `default` is returned. If the value
            is not found and `default` is `None`, the default value of 
            `Config.configuration` is returned if set else `None` is returned.
        """
        if self.has_option(section,key):
            flist = self.keyfile.get_double_list(section,key)
            if flist is not None:
                ret = []
                for f in flist:
                    ret.append(f)
                return ret
        if default is None:
            try:
                return self.configuration[section][key]['default']
            except:
                return None
        return default
    
    def get_string(self,section,key,default=None):
        """
        Get a string option from KeyFile.

        :param section: Section/group the option is in.
        :type section: `str`
        :param key: The name of the option.
        :type key: `str`
        :param default: The default value to return if the lookup fails.
        :type default: `str` or `None`
        :returns: The option value if found in KeyFile. If the value is not
            found and `default` is not `None`, `default` is returned. If the value
            is not found and `default` is `None`, the default value of 
            `Config.configuration` is returned if set else `None` is returned.
        """
        if self.has_option(section,key):
            return self.keyfile.get_string(section,key)
        if default is None:
            try:
                return self.configuration[section][key]['default']
            except:
                return None
            
        return default
    
    def get_string_list(self,section,key,default=None):
        """
        Get a boolean option from KeyFile.

        :param section: Section/group the option is in.
        :type section: `str`
        :param key: The name of the option.
        :type key: `str`
        :param default: The default value to return if the lookup fails.
        :type default: `list(str)` or `None`
        :returns: The option value if found in KeyFile. If the value is not
            found and `default` is not `None`, `default` is returned. If the value
            is not found and `default` is `None`, the default value of 
            `Config.configuration` is returned if set else `None` is returned.
        """
        if self.has_option(section,key):
            slist = self.keyfile.get_string_list(section,key)
            if slist is not None:
                ret = []
                for s in slist:
                    ret.append(s)
                return ret
        if default is None:
            try:
                return self.configuration[section][key]['default']
            except:
                return []
        return default
    
    def get_locale_string(self,section,key,locale):
        """
        Get a localized string form KeyFile.

        :param section: The section/group the localized string is in.
        :type section: `str`
        :param key: The option name.
        :type key: `str`
        :param locale: The locale to look up.
        :type locale: `str`
        :returns: A localized string if found in KeyFile or `None` if not found.
        """
        try:
            return self.keyfile.get_locale_string(section,key,locale)
        except:
            pass
        return None
    
    def get_locale_string_list(self,section,key,locale=None):
        """
        Get a localized string list form KeyFile.

        :param section: The section/group the localized string is in.
        :type section: `str`
        :param key: The option name.
        :type key: `str`
        :param locale: The locale to look up.
        :type locale: `str`
        :returns: A localized string list if found in KeyFile or `None` if not found.
        """
        slist = self.keyfile.get_locale_string_list(section,key,locale)
        if slist is not None:
            ret = []
            for s in slist:
                ret.append(s)
            return ret
        return None
    
    def set(self,section,key,value:str):
        """
        Set a raw value in KeyFile.

        :param section: The section the option is in.
        :type section: `str`
        :param key: The key/option to set.
        :type key: `str`
        :param value: The value to set.
        :type value: `str`
        """
        self.keyfile.set_value(section,key,value)

    def set_boolean(self,section,key,value:bool):
        """
        Set a boolean value in KeyFile.

        :param section: The section the option is in.
        :type section: `str`
        :param key: The key/option to set.
        :type key: `str`
        :param value: The value to set.
        :type value: `bool`
        """
        self.keyfile.set_boolean(section,key,value)

    def set_boolean_list(self,section,key,value):
        """
        Set a boolean list value in KeyFile.

        :param section: The section the option is in.
        :type section: `str`
        :param key: The key/option to set.
        :type key: `str`
        :param value: The value to set.
        :type value: `list(bool)`
        """
        self.keyfile.set_boolean_list(section,key,value)

    def set_integer(self,section,key,value:int):
        """
        Set an integer value in KeyFile.

        :param section: The section the option is in.
        :type section: `str`
        :param key: The key/option to set.
        :type key: `str`
        :param value: The value to set.
        :type value: `int`
        """
        self.keyfile.set_int64(section,key,value)

    def set_integer_list(self,section,key,value):
        """
        Set an integer list value in KeyFile.

        :param section: The section the option is in.
        :type section: `str`
        :param key: The key/option to set.
        :type key: `str`
        :param value: The value to set.
        :type value: `list(int)`
        """
        self.keyfile.set_int64_list(section,key,value)

    def set_float(self,section,key,value:float):
        """
        Set a float value in KeyFile.

        :param section: The section the option is in.
        :type section: `str`
        :param key: The key/option to set.
        :type key: `str`
        :param value: The value to set.
        :type value: `float`
        """
        self.keyfile.set_double(section,key,value)

    def set_float_list(self,section,key,value):
        """
        Set a float list value in KeyFile.

        :param section: The section the option is in.
        :type section: `str`
        :param key: The key/option to set.
        :type key: `str`
        :param value: The value to set.
        :type value: `list(float)`
        """
        self.keyfile.set_double_list(section,key,value)

    def set_string(self,section,key,value):
        """
        Set a string value in KeyFile.

        :param section: The section the option is in.
        :type section: `str`
        :param key: The key/option to set.
        :type key: `str`
        :param value: The value to set.
        :type value: `str`
        """
        self.keyfile.set_string(section,key,value)

    def set_string_list(self,section,key,value):
        """
        Set a string list value in KeyFile.

        :param section: The section the option is in.
        :type section: `str`
        :param key: The key/option to set.
        :type key: `str`
        :param value: The value to set.
        :type value: `list(str)`
        """
        self.keyfile.set_string_list(section,key,value)

    def set_locale_string(self,section,key,locale,value):
        """
        Set a localized string in KeyFile.

        :param section: The section the option is in.
        :type section: `str`
        :param key: The key/option to set.
        :type key: `str`
        :param locale: The locale the string belongs to.
        :type locale: `str`
        :param value: The value to set.
        :type value: `str`
        """
        self.keyfile.set_locale_string(section,key,locale,value)

    def set_locale_string_list(self,section,key,locale,value):
        """
        Set a localized string list in KeyFile.

        :param section: The section the option is in.
        :type section: `str`
        :param key: The key/option to set.
        :type key: `str`
        :param locale: The locale the string belongs to.
        :type locale: `str`
        :param value: The value to set.
        :type value: `list(str)`
        """
        self.keyfile.set_locale_string_list(section,key,locale,value)

    def remove(self,section,key):
        """
        Remove an option from KeyFile.

        :param section: The section/group the option is in.
        :type section: `str`
        :param key: The key/option to remove.
        :type key: `str`
        """
        if self.has_option(section,key):
            self.keyfile.remove_key(section,key)
    
    def remove_section(self,section):
        """
        Remove a section/group from KeyFile.

        This is the same as :func:`Config.remove_group`.
        
        :param section: The section/group to remove.
        :type section: `str`
        """
        if self.has_section(section):
            self.keyfile.remove_group(section)

    def remove_group(self,group):
        """
        Remove a section/group from KeyFile.

        This is the same as :func:`Config.remove_section`.
        
        :param group: The section/group to remove.
        :type group: `str`
        """
        if self.has_section(group):
            self.keyfile.remove_group(group)

    @GObject.Property
    def raw_variables(self):
        """
        Get *raw* variables. The variables returned are only those
        set in the KeyFile.

        :returns: A `dict` containing the variables.
        """
        vars={}
        if self.has_section('variables'):
            for key in self.keyfile.get_keys('variables')[0]:
                vars[key] = self.keyfile.get_string('variables',key)
        return vars
    
    @GObject.Property
    def variables(self):
        """
        Returns the variables for template strings.
        The variables are those from the environment and those 
        set in KeyFile. There are also some sextra variables set:
        * `BACKUP_DIR` - the backup directory.
        * `DOCUMENTS` - user documents directory.
        * `HOME` - user home directory.
        * `USER_DOCUMENTS_DIR` - user documents directory.
        * `USER_HOME_DIR` - user home directory.

        :returns: A `dict` containing the variables.
        """
        vars = dict(os.environ)

        vars.update(self.raw_variables)

        vars.update({
            "USER_HOME_DIR":self.user_home_dir,
            "HOME":self.user_home_dir,
            "USER_DOCUMENTS_DIR":self.user_documents_dir,
            "DOCUMENTS": self.user_documents_dir,
            "BACKUP_DIR": self.backup_dir
        })
        return vars
    
    def get_variable(self,variable,default=None):
        """
        Get a single variable.

        :param variable: The name of the variable.
        :type variable: `str`
        :param default: The default value to return 
            if the variable is not set.
        :type default: `str` or `None`
        :returns: The variable value if set, the
            `default` if given and the variable is not set.
            Else this method returns an empty string.
        """
        if self.has_option('variables',variable):
            return self.keyfile.get_string('variables',variable)
        if default:
            return default
        return ""
    
    def set_variable(self,variable:str,value:str):
        """
        Sets a variable.

        :param variable: The name of the variable.
        :type variable: `str`
        :param value: The value of the variable.
        :type value: `str`
        """
        self.keyfile.set_string('variables',variable,value)

    def remove_variable(self,variable):
        """
        Remove a variable from KeyFile.

        :param variable: The name of the variable to remove.
        :type variable: `str`
        """
        if self.has_option('variables',variable):
            self.keyfile.remove_key('variables',variable)

    def save(self):
        """
        Save the configuration set in the KeyFile to a file on disk.

        This method emits the `save` signal.
        """
        self.emit("save")

    def do_save(self):
        """
        The real work of saving the configuration to file is done in this method.

        **Do not call this method yourself!** Use the method :func:`Config.save` instead!
        """
        for sname,sect in self.configuration.items():
            if sname not in ('sgbackup','zipfileArchiver','commandGame') and isinstance(sect,dict):
                for key,spec in sect.items():
                    if not isinstance(spec,dict):
                        continue

                    if not self.has_option(sname,key) and 'type' in spec:
                        if spec['type'] in ('bool','boolean'):
                            if 'default' in spec:
                                self.set_boolean(sname,key,spec['default'])
                            else:
                                self.set_boolean(sname,key,False)
                        elif spec['type'] in ('bool-list','boolean-list'):
                            if 'default' in spec:
                                self.set_boolean_list(sname,key,spec['default'])
                            else:
                                self.set_boolean_list(sname,key,[False])
                        elif spec['type'] in ('int','integer'):
                            if 'default' in spec:
                                self.set_integer(sname,key,spec['default'])
                            else:
                                self.set_integer(spec,key,0)
                        elif spec['type'] in ('int-list','integer-list'):
                            if 'default' in spec:
                                self.set_integer_list(sname,key,spec['default'])
                            else:
                                self.set_integer_list(sname,key,[0])
                        elif spec['type'] == 'float':
                            if 'default' in spec:
                                self.set_float(sname,key,spec['default'])
                            else:
                                self.set_float(sname,key,0.0)
                        elif spec['type'] == 'float-list':
                            if 'default' in spec:
                                self.set_float_list(sname,key,spec['default'])
                            else:
                                self.set_float_list(sname,key,[0.0])
                        elif spec['type'] in ('str','string'):
                            if 'default' in spec:
                                self.set_string(sname,key,spec['default'])
                            else:
                                self.set_string(sname,key,"")
                        elif spec['type'] in ('str-list','string-list'):
                            if 'default' in spec:
                                self.set_string_list(sname,key,spec['default'])
                            else:
                                self.set_string_list(self,key,[''])
                        else:
                            print("Unknown config-type \"{type}\", skipping!",type=spec['type'])
                            continue

        self.keyfile.save_to_file(self.user_config)
        os.chmod(self.user_config,self.get_integer('sgbackup','configPermission'))
        
    def load_config(self,config_file):
        """
        Load configration from an alternate file.

        This method emits the `load-config` signal if there are changes
        to the config file.
        """
        if os.path.isfile(self.config_file):
            kf = GLib.KeyFile.new()
            kf.load_from_file(config_file)

            kf_groups = kf.get_groups()
            if not kf_groups or not kf_groups[0]:
                return
            for group in kf_groups[0]:
                kf_keys = kf.get_keys(group)
                if not kf_keys or not kf_keys[0]:
                    continue
                for key in kf_keys[0]:
                    self.set(group,key,kf.get_value(group,key))

            self.emit("load-config")

    def do_load_config(self):
        """
        The `load-config` signal callback.
        
        **Do not call thais method yourself!**
        """
        pass

    def destroy(self):
        """
        Destroy the instance of this class.

        Normally there should be no reason to call this method yourself!

        This method is called when the :class:`sgbackup.application.Application` 
        instance is destroyed.
        """
        self.emit('destroy')

    def do_destroy(self):
        """
        The `destroy` signal callback.

        **Never call this method yourself!**
        """
        if self.__app:
            self.__app = None
