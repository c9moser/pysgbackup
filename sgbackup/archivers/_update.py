import os
import sys
from .. import config

if sys.platform == 'win32':
    def update(global_archivers=False):
        verbose = config.CONFIG['verbose']
        
        global_archivers_dir = config.CONFIG['global-archivers-dir']
        if global_archivers:
            archivers_dir = global_archivers_dir
        else:
            archivers_dir = config.CONFIG['user-archivers-dir']
        
        if verbose:
            print("<archiver:directory> {0}".format(archivers_dir))
            
        #check if we are installed with msys or similar
        if os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))) == 'bin':
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
            usr_bin = os.path.join(root_dir,'usr','bin')
            
            # check for msys or similar
            if os.path.isdir(usr_bin):
                replace={}
                if (verbose):
                    print("<archiver:check> cygpath")
                if os.path.isfile(os.path.join(usr_bin,'cygpath.exe')):
                    replace={'__CYGPATH__': os.path.join(usr_bin,'cygpath.exe')}
                
                #check for tar
                if (verbose):
                    print("<archiver:check> tar")
                if os.path.isfile(os.path.join(usr_bin,'tar.exe')):
                    replace['__EXECUTABLE__']=os.path.join('tar.exe')
                    tar_archivers=['tar','tar.bz2','tar.gz','tar.xz','tbz','tgz','txz']
                    for i in tar_archivers:
                
                        print("<archiver:update> {0}.archiver".format(i))
                        archiver_in=os.path.join(global_archivers_dir,'.'.join((i,'archiver','w32','in')))
                        archiver_out=os.path.join(archivers_dir,'.'.join((i,'archiver')))
                        
                        with open(archiver_in,'r') as ifile:
                            s=ifile.read()
                            
                        for k,v in replace.items():
                            s=s.replace(k,v)
                            
                        with open(archiver_out,'w') as ofile:
                            ofile.write(s)
                            
        #check for WinRAR
        winrar_exe = None 
        if verbose:
            print("<archiver:check> WinRAR")
        if os.path.isfile(os.path.expandvars(os.path.join("${SystemDrive}","Program Files","WinRAR","WinRAR.exe"))):
            winrar_exe = os.path.expandvars(os.path.join("${SystemDrive}","Program Files","WinRAR","WinRAR.exe"))
        if (not winrar_exe 
            and os.path.isfile(os.path.expandvars(os.path.join("${SystemDrive}","Program Files (X86)","WinRAR","WinRAR.exe")))):
            winrar_exe = os.path.expandvars(os.path.join("${SystemDrive}","Program Files (X86)","WinRAR","WinRAR.exe"))
            
        if winrar_exe:
            print("<archiver:update> rar.archiver")
            replace={'__EXECUTABLE__':winrar_exe}
            
            with open(os.path.join(global_archivers_dir,'rar.archiver.w32.in'),'r') as ifile:
                s=ifile.read()
                            
            for k,v in replace.items():
                s=s.replace(k,v)
                
            with open(os.path.join(archivers_dir,'rar.archiver'),'w') as ofile:
                ofile.write(s)
        
        #check for 7-Zip
        sevenzip_exe = None
        if verbose:
            print("<archiver:check> 7-Zip")
        if os.path.isfile(os.path.expandvars(os.path.join("${SystemDrive}","Program Files", "7-Zip","7z.exe"))):
            sevenzip_exe = os.path.expandvars(os.path.join("${SystemDrive}","Program Files", "7-Zip","7z.exe"))
        if (not sevenzip_exe 
            and os.path.isfile(os.path.expandvars(os.path.join("${SystemDrive}","Program Files (X86)", "7-Zip","7z.exe")))):
            sevenzip_exe = os.path.expandvars(os.path.join("${SystemDrive}","Program Files (X86)", "7-Zip","7z.exe"))
            
        if sevenzip_exe:
            print("<archiver:update> 7z.archiver")
            replace={'__EXECUTABLE__':sevenzip_exe}
            
            with open(os.path.join(global_archivers_dir,'7z.archiver.w32.in'),'r') as ifile:
                s=ifile.read()
                
            for k,v in replace.items():
                s=s.replace(k,v)
                
            with open(os.path.join(global_archivers_dir,'7z.archiver'),'w') as ofile:
                ofile.write(s)
    # update()
    
else:
    def update(global_archivers=False):
        global_archivers_dir = config.CONFIG['global-archivers-dir']
        if (global_archivers):
            archivers_dir = global_archivers_dir
        else:
            archivers_dir = config.CONFIG['user-archivers-dir']
        
        def _find_in_path(program):
            path = os.environ['PATH'].split(':')
            
            for p in path:
                f = os.path.join(p,prog)
                if os.path.isfile(f):
                    return f
        
            return ''
            
        # check for tar
        tar_exe = _find_in_path('tar')
        if (tar_exe):
            tar_archivers = ['tar','tar.bz2','tar.gz','tar.xz','tbz','tgz','txz']
            replace = {'__EXECUTABLE__':tar_exe}
            for i in tar_archivers:
                with open(os.path.join(global_archivers_dir,'.'.join((i,'archiver','in'))), 'r') as ifile:
                    s = ifile.read()
                    
                for k,v in replace.items():
                    s.replace(k,v)
                    
                with open(os.path.join(archivers_dir,'.'.join((i,'archiver'))),'w') as ofile:
                    ofile.write(f)
                    
        #TODO: check for 7z
    # udpate()

