from ..command import Command,CommandOptions
from ..error import OptionError
from ..help import get_builtin_help
from gi.repository import GLib

import os
import sys

if sys.platform == 'win32':
    PLATFORM_WINDOWS = True
    import winreg
else:
    PLATFORM_WINDOWS = False

class ArchiverOptions(CommandOptions):
    (
        MODE_GET,
        MODE_LIST,
        MODE_SCAN,
        MODE_SET
    ) = range(4)

    def __init__(self,app,cmd,mode=MODE_GET):
        CommandOptions.__init__(self,app,'archiver',cmd)
        self.__mode = mode
        self.__archiver = None

    @property
    def archiver(self):
        return self.__archiver
    @archiver.setter
    def archiver(self,archiver:str):
        if self.application.archivers.has_archiver(archiver):
            self.__archiver = archiver
        else:
            raise OptionError("\"{archiver}\" is not a valid archiver!")
        
    @property
    def mode(self):
        return self.__mode
    @mode.setter
    def mode(self,mode:int):
        self.__mode = mode

class Archiver(Command):
    def __init__(self,app):
        Command.__init__(self,app,'archiver','list,set,scan archivers')

    def get_synopsis(self, command=None):
        return "sgbackup {command} [get|list|scan]\nsgbackup {command} set <ARCHIVER>".format(command=command)
    
    def get_help(self, command=None):
        if command is None:
            command = self.id

        archivers = ""
        for i in sorted((j.id for j in self.application.archivers.get_archivers())):
            archivers += "    {}\n".format(i)

        variables={'ARCHIVERS':archivers}

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,variables)
    
    def create_archiver_file(
            self,
            filename,
            name,
            exe,
            ext,
            alt_exts,
            backup_args,
            restore_args,
            change_dir,
            verbose=None,
            variables=None,
            cygpath=None,
            multiprocessing=False):
        
        if not os.path.isabs(filename):
            filename = os.path.join(self.application.config.archiver_dir,filename)
        if not filename.endswith('.archiver'):
            filename += ".archiver"
        
        if PLATFORM_WINDOWS:
            filename = filename.replace('/','\\')
        
        kf = GLib.KeyFile.new()
        section = 'archiver'
        kf.set_string(section,'name',name)
        kf.set_string(section,'executable',exe)
        kf.set_string(section,'extension',ext)
        if alt_exts:
            kf.set_string_list(section,'altExtensions',alt_exts)
        kf.set_string(section,'backupArgs',backup_args)
        kf.set_string(section,'restoreArgs',restore_args)
        if verbose:
            kf.set_string(section,'verbose',verbose)
        kf.set_boolean(section,'changeDirectory',change_dir)
        if cygpath:
            kf.set_string(section,'cygpath',cygpath)
        kf.set_boolean(section,"multiprocessing",multiprocessing)

        if variables:
            for vname,vvalue in variables.items():
                kf.set_string('variables',vname,vvalue)

        kf.save_to_file(filename)

    def scan_windows_winrar(self):
        if not PLATFORM_WINDOWS:
            return False
        
        try:
            rk = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE,"Software\\WinRAR")
            exe = None
            try:
                
                rval,rtype = winreg.QueryValueEx(rk,"exe64")
                if (rtype == winreg.REG_SZ):
                    exe = rval
            except:
                try:
                    rval,rtype = winreg.QueryValueEx(rk,'exe')
                    if (rtype == winreg.REG_SZ):
                        exe = rval
                except:
                    pass

            winreg.CloseKey(rk)
        except:
            return False
        
        if not exe:
            return False
        
        self.create_archiver_file(
            'WinRAR.archiver',
            'winrar',
            exe,
            'rar',
            [],
            "a -r -ibck -ed -ma${RAR_VERSION} -mt${PROCESS_MAX} -m${RAR_COMPRESSION} -k -s \"${FILENAME}\" \"${SAVEGAME_DIR}\"",
            "x -r -ibck \"${FILENAME}\"",
            True,
            variables={
                'RAR_VERSION':'5',
                'RAR_COMPRESSION': '5',
            },
            multiprocessing=True
        )
        return True

    def scan_windows_7zip(self):
        if not PLATFORM_WINDOWS:
            return False

        try:
            rk = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE,"Software\\7-Zip")
            path = None
            try:
                rval,rtype = winreg.QueryValueEx(rk,'Path64')
                if rtype == winreg.REG_SZ:
                    path = rval
            except:
                try:
                    rval,rtype = winreg.QueryValueEx(rk,'Path')
                    if rtype == winreg.REG_SZ:
                        path = rval
                except:
                    pass

            winreg.CloseKey(rk)
        except:
            return False
        
        if not path or not os.path.isdir(path):
            return False
        
        exe = os.path.join(path,'7z.exe').replace('/','\\')
        if not os.path.isfile(exe):
            return False
        
        self.create_archiver_file(
            '7zip.archiver',
            '7zip',
            exe,
            '7z',
            [],
            "a -t7z -r \"${FILENAME}\" \"${SAVEGAME_DIR}\"",
            "x -r \"${FILENAME}\"",
            True
        )
        return True

    def scan_windows_msys_tar(self):
        msys_bindir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))),'usr','bin')
        if not os.path.isdir(msys_bindir):
            return False
        
        msys_cygpath = os.path.join(msys_bindir,'cygpath.exe').replace('/','\\')
        msys_tar = os.path.join(msys_bindir,'tar.exe').replace('/','\\')

        if not os.path.isfile(msys_cygpath) or not os.path.isfile(msys_tar):
            return False
        
        # tar
        self.create_archiver_file(
            'tar.archiver',
            'tar',
            msys_tar,
            'tar',
            [],
            "-cC \"${SAVEGAME_ROOT}\" ${VERBOSE} -f \"${FILENAME}\" \"${SAVEGAME_DIR}\"",
            "-xC \"${SAVEGAME_ROOT}\" ${VERBOSE} -f \"${FILENAME}\"",
            False,
            '-v',
            None,
            msys_cygpath
        )

        #tar xz
        self.create_archiver_file(
            'txz.archiver',
            'tar:xz',
            msys_tar,
            'txz',
            ['tar.xz'],
            "-cJC \"${SAVEGAME_ROOT}\" ${VERBOSE} -f \"${FILENAME}\" \"${SAVEGAME_DIR}\"",
            "-xJC \"${SAVEGAME_ROOT}\" ${VERBOSE} -f \"${FILENAME}\"",
            False,
            '-v',
            None,
            msys_cygpath
        )

        self.create_archiver_file(
            'tbz.archiver',
            'tar:bzip2',
            msys_tar,
            'tbz',
            ['tar.bz'],
            "-cjC \"${SAVEGAME_ROOT}\" ${VERBOSE} -f \"${FILENAME}\" \"${SAVEGAME_DIR}\"",
            "-xjC \"${SAVEGAME_ROOT}\" ${VERBOSE} -f \"${FILENAME}\"",
            False,
            '-v',
            None,
            msys_cygpath
        )

        self.create_archiver_file(
            'tz.archiver',
            'tar:z',
            msys_tar,
            'tz',
            ['tar.z'],
            "-cZC \"${SAVEGAME_ROOT}\" ${VERBOSE} -f \"${FILENAME}\" \"${SAVEGAME_DIR}\"",
            "-xZC \"${SAVEGAME_ROOT}\" ${VERBOSE} -f \"${FILENAME}\"",
            False,
            '-v',
            None,
            msys_cygpath
        )

        self.create_archiver_file(
            'tgz.archiver',
            'tar:gz',
            msys_tar,
            'tgz',
            ['tar.gz'],
            "-czC \"${SAVEGAME_ROOT}\" ${VERBOSE} -f \"${FILENAME}\" \"${SAVEGAME_DIR}\"",
            "-xzC \"${SAVEGAME_ROOT}\" ${VERBOSE} -f \"${FILENAME}\"",
            False,
            '-v',
            None,
            msys_cygpath
        )

    def scan_windows(self):
        ret = False

        if self.scan_windows_winrar():
            ret = True
        if self.scan_windows_7zip():
            ret = True
        if self.scan_windows_msys_tar():
            ret = True

        return ret
    
    def scan_unix(self):
        return False
    
    def parse_vfunc(self, cmd, argv):
        options = ArchiverOptions(self.application,cmd)

        if len(argv):
            if argv[0] == 'get':
                options.mode = ArchiverOptions.MODE_GET 
            elif argv[0] == 'list':
                options.mode = ArchiverOptions.MODE_LIST
                if len(argv) > 1:
                    print("!!! \"sgbackup {command} list\" does not take any arguments! Ignoring extra arguments.".format(command=cmd),file=sys.stderr)
            elif argv[0] == 'scan':
                options.mode = ArchiverOptions.MODE_SCAN
                if len(argv) > 1:
                    print("!!! \"sgbackup {command} scan\" does not take any arguments! Ignoring extra arguments.".format(command=cmd),file=sys.stderr)
            elif argv[0] == 'set':
                if len(argv) < 2:
                    raise OptionError("!!! \"sgbackup {command} set\" needs a archiver as an argument!".format(command=cmd))
                options.mode = ArchiverOptions.MODE_SET
                options.archiver = argv[1]
        return options
    
    def execute_vfunc(self, options):
        if options.mode == ArchiverOptions.MODE_GET:
            print(self.application.archivers.standard_archiver.id)
            return 0
        elif options.mode == ArchiverOptions.MODE_LIST:
            archivers = [i.id for i in self.application.archivers.get_archivers()]
            archivers.sort()
            for i in archivers:
                print(i)
            return 0
        elif options.mode == ArchiverOptions.MODE_SET:
            self.application.archivers.standard_archiver = options.archiver
            self.application.config.save()
            return 0
        elif options.mode == ArchiverOptions.MODE_SCAN:
            reload=False
            if PLATFORM_WINDOWS:
                reload = self.scan_windows()
            else:
                reload = self.scan_unix()
            if reload:
                self.application.archivers.load_command_archivers()
            return 0
        return 1
    
COMMANDS = [
    (Archiver,None),
]