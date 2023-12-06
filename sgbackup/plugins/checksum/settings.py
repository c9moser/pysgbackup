
import sys
import os
import subprocess

PLUGIN_ID="checksum"

if sys.platform == 'win32':
    REQUIRE_CYGPATH = True
else:
    REQUIRE_CYGPATH = False

CHECKSUMS = [
    'b2sum',
    'md5sum',
    'sha1sum',
    'sha224sum',
    'sha256sum',
    'sha384sum',
    'sha512sum'
]

__file_validate = lambda x: (os.path.isfile(x) or x == "")
def __checksum_validate(slist):
    for i in slist:
        if i not in CHECKSUMS:
            return False
    return True

OPTIONS= {
    PLUGIN_ID: {
        'requireCygpath': {'type':'boolean','default':REQUIRE_CYGPATH,'validate':lambda x: (REQUIRE_CYGPATH == bool(x))},
        'cygpath':{'type':'string','default':'','validate':__file_validate},
        'b2sum':{'type':'string','default':'','validate':__file_validate},
        'md5sum':{'type':'string','default':'','validate':__file_validate},
        'sha1sum':{'type':'string','default':'','validate':__file_validate},
        'sha224sum':{'type':'string','default':'','validate':__file_validate},
        'sha256sum':{'type':'string','default':'','validate':__file_validate},
        'sha384sum':{'type':'string','default':'','validate':__file_validate},
        'sha512sum':{'type':'string','default':'','validate':__file_validate},
        'checksums':{'type':'string-list','default':[],'validate':__checksum_validate},
        'checksum_create_flags':{'type':'string','default':'--binary --tag'},
        'checksum_check_flags':{'type':'string','default':'--check --status'},
    },
}

def get_config_options():
    sect = PLUGIN_ID
    print(sect)
    if REQUIRE_CYGPATH:
        testdir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))),"usr","bin")
        print(testdir)
        if os.path.isdir(testdir):
            cygpath = os.path.join(testdir,'cygpath.exe')
            
            if os.path.isfile(cygpath):
                OPTIONS[sect]['cygpath']['default'] = cygpath.replace('/','\\')
            else:
                return
            
            b2sum = os.path.join(testdir,'b2sum.exe')
            md5sum = os.path.join(testdir,'md5sum.exe')
            sha1sum = os.path.join(testdir,'sha1sum.exe')
            sha224sum = os.path.join(testdir,'sha224sum.exe')
            sha256sum = os.path.join(testdir,'sha256sum.exe')
            sha384sum = os.path.join(testdir,'sha384sum.exe')
            sha512sum = os.path.join(testdir,'sha512sum.exe')

            if os.path.isfile(b2sum):
                OPTIONS[sect]['b2sum']['default'] = b2sum.replace("/","\\")
            if os.path.isfile(md5sum):
                OPTIONS[sect]['md5sum']['default'] = md5sum.replace("/","\\")
            if os.path.isfile(sha1sum):
                OPTIONS[sect]['sha1sum']['default'] = sha1sum.replace("/","\\")
            if os.path.isfile(sha224sum):
                OPTIONS[sect]['sha224sum']['default'] = sha224sum.replace('/','\\')
            if os.path.isfile(sha256sum):
                OPTIONS[sect]['sha256sum']['default'] = sha256sum.replace('/','\\')
            if os.path.isfile(sha384sum):
                OPTIONS[sect]['sha384sum']['default'] = sha384sum.replace('/','\\')
            if os.path.isfile(sha512sum):
                OPTIONS[sect]['sha512sum']['default'] = sha512sum.replace("/","\\")
    else:
        for cksum in CHECKSUMS:
            proc = subprocess.run(['which',cksum],capture_output=True)
            if proc.returncode == 0:
                OPTIONS[sect][cksum]['default'] = proc.stdout.decode('utf-8')

            

    return OPTIONS
