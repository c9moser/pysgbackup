from ..command import Command,CommandOptions
from ..error import OptionError
from ..help import get_builtin_help

class VariableOptions(CommandOptions):
    ID = 'variable'
    MODES = ('list','get','set','delete')

    def __init__(self,app,cmd):
        CommandOptions.__init__(self,app,'variable',cmd)
        self.__mode = 'list'
        self.__variable=None
        self.__value=None

    @property
    def mode(self):
        return self.__mode
    @mode.setter
    def mode(self,m:str):
        if not m in self.MODES:
            raise ValueError("Unknown mode \"{mode}\"!".format(mode=m))
        self.__mode = m
        
    @property
    def variable(self):
        return self.__variable
    @variable.setter
    def variable(self,var:str):
        self.__variable = var

    @property
    def value(self):
        return self.__value
    @value.setter
    def value(self,val:str):
        self.__value = val


class Variable(Command):
    def __init__(self,app):
        Command.__init__(self,app,VariableOptions.ID,"Get|set|list variables.")

    def get_synopsis(self,command=None):
        if command is None:
            command = self.id
        return """sgbackup {command} [list]
sgbackup {command} delete VARIABLE_NAME
sgbackup {command} get VARIABLE_NAME
sgbackup {command} set VARIABLE_NAME VARIABLE_VALUE""".format(command=command)
    
    def get_help(self,command=None):
        if command is None:
            command = self.id

        return get_builtin_help(self.id,command,self.get_help_synopsis(command),None,None)
    
    def parse_vfunc(self,command,argv):
        options = VariableOptions(self.application,command)
        if len(argv) == 0:
            return options
        
        try:
            options.mode = argv[0]
        except Exception as err:
            raise OptionError("Illegal mode! ({reason})".format(reason=err))
        
        if options.mode == 'list':
            pass
        elif options.mode in ("get","delete"):
            if len(argv) < 2:
                raise OptionError("\"sgbackup {command} {mode}\" needs a VARIABLE_NAME!".format(command=command,mode=options.mode))
            options.variable = argv[1]
        elif options.mode == "set":
            if len(argv) < 3:
                raise OptionError(
                    "\"sgbackup {command} {mode}\" needs a VARIABLE_NAME and a VARIABLE_VALUE!".format(
                        command=command,mode=options.mode))
            options.variable = argv[1]
            options.value = argv[2]
        
        return options
    
    def execute_vfunc(self, options:VariableOptions):
        if options.mode == 'list':
            for variable,value in self.application.config.raw_variables.items():
                print("{}={}".format(variable,value))
            
            return 0
        elif options.mode == 'delete':
            self.application.config.remove_variable(options.variable)
            self.application.config.save()
            return 0
        elif options.mode == 'get':
            print(self.application.config.get_variable(options.variable,default=""))
            return 0
        elif options.mode == 'set':
            self.application.config.set_variable(options.variable,options.value)
            self.application.config.save()
            return 0
        return 1
    
COMMANDS=[
    (Variable,['var'])
]
