
class FtpConnectionError(Exception):
    def __init__(self,message="",*args):
        Exception.__init__(self,message,*args)

    @property
    def message(self):
        return self.args[0]