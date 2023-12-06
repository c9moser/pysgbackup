# -*- conding: utf-8 -*-
# Author: Chrstian Moser
# License: GPL
# File: sgbackup/steam.py
# Module: sgbackup.steam

import os
import sys
import glob

from gi.repository import GObject

def steam_parse_acf(filename):
    if not os.path.isfile(filename) or not filename.endswith('.acf'):
        return None
    
    acf = {}
    acf['LibraryPath'] = os.path.dirname(os.path.dirname(filename))

    with open(filename,'r') as ifile:
        line = ""
        while not line:
            line = str(ifile.readline()).strip()

        if not line.startswith("\"AppState\""):
            return None
        if '{' not in line:
            while '{' not in line:
                line = ifile.readline().strip()
                if line and not '{' in line:
                    return None
        
        sections=[acf]

        last_key = "AppState"

        for line in (str(i).strip() for i in ifile.readlines()):
            if not line:
                continue

            if line == "{":
                sections[-1][last_key] = {}
                sections.append(sections[-1][last_key])
            elif line == "}":
                del sections[-1]
                if len(sections) == 0:
                    break
            else:
                parse = line.split("\"")
                if len(parse) == 3:
                    last_key = parse[1]
                    if '{' in line:
                        sections[-1][last_key] = {}
                        sections.append(sections[-1][last_key])
                elif len(parse) == 5:
                    key = parse[1]
                    value = parse[3]
                    sections[-1][key] = value

    return acf
# steam_parse_acf()

class SteamAppidIgnore(GObject.GObject):
    __gsginals__ = {
        'destroy': (GObject.SIGNAL_RUN_FIRST,None,())
    }

    def __init__(self,app):
        GObject.GObject.__init__(self)
        self.__app = None
        self.__appids=[]

    def _real_initialize(self,app):
        self.__app = app

        if os.path.isfile(self.ignore_file):
            with open(self.ignore_file,'r') as ifile:
                lineno = 0
                for line in (str(i).strip() for i in ifile.readlines()):
                    lineno += 1
                    if not line or line.startswith('#'):
                        continue
                    try:
                        appid = int(line)
                        if not appid in self.__appids:
                            self.add(appid)
                    except Exception as err:
                        print("AppidIgnore parse error in [{file}:{line}]! ({message})".format(
                                file=self.ignore_file,line=lineno,message=err.args[0]),
                              file=sys.stderr)

    @GObject.Property
    def ignore_file(self):
        return os.path.join(self.application.config.user_config_dir,'steamapp-ignore.lst')
    
    @GObject.Property
    def application(self):
        return self.__app
    
    @GObject.Property
    def appids(self):
        return self.__appids

    def save(self):
        with open(self.ignore_file,'w') as ofile:
            for i in self.appids:
                ofile.write("{}\n".format(i))

    def add(self,appid:int):
        if not appid in self.__appids:
            self.__appids.append(appid)
        self.__appids.sort()


    def remove(self,appid:int):
        if appid in self.__appids:
            for i in range(len(self.__appids)):
                if self.__appids[i] == appid:
                    del self.__appids[i]
                    return

    def destroy(self):
        self.emit('destroy')

    def do_destroy(self):
        self.__app = None

class SteamLib(GObject.GObject):
    __gsignals__ = {
        'destroy': (GObject.SIGNAL_RUN_FIRST,None,())
    }

    def __init__(self,app,path):
        GObject.GObject.__init__(self)
        self.__app = app
        if (os.path.isdir(path)):
            if sys.platform == "win32":
                temp = path.replace("/","\\")
                if temp.endswith("\\"):
                    self.__path = temp[:-1]
                else:
                    self.__path = temp
            else:
                if path.endswith("/"):
                    self.__path = path[:-1]
                else:
                    self.__path = path
        else:
            self.__path = None

    @GObject.Property
    def application(self):
        return self.__app
    
    @GObject.Property
    def is_valid(self):
        return (self.__path and os.path.isdir(self.__path))
    
    @GObject.Property
    def path(self):
        return self.__path

    @GObject.Property
    def apps(self):
        apps={}
        for fn in glob.glob(os.path.join(self.path,"steamapps","appmanifest_*.acf")):
            basename = os.path.basename(fn)
            appid=int(basename[len('appmanifest_'):-4])
            acf = steam_parse_acf(fn)
            if 'appid' in acf and 'name' in acf and 'installdir' in acf:
                apps[appid] = acf
        return apps

    @GObject.Property
    def registered_apps(self):
        apps = {}
        for appid,acf in self.apps.items():
            if appid in self.application.games.steam_ids:
                apps[appid] = acf
            
        return apps

    @GObject.Property
    def unregistered_apps(self):
        apps = self.apps
        unregistered = {}
        for appid,acf in apps.items():
            if appid not in self.application.games.steam_ids and appid not in self.application.steam.ignore_appids:
                unregistered[appid] = acf

        return unregistered
    
    @GObject.Property
    def appids(self):
        appids = [int(os.path.basename(i)[len('appmanifest_'):-4]) for i in 
                    glob.glob(os.path.join(self.path,"steamapps","appmanifest_*.acf"))]
        appids.sort()
        return appids

    
    def destroy(self):
        self.emit('destroy')

    def do_destroy(self):
        self.__app = None

class Steam(GObject.GObject):
    __gsignals__ = {
        'destroy': (GObject.SIGNAL_RUN_FIRST,None,())
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.__app = None
        self.__libraries=[]
        self.__appid_ignore = SteamAppidIgnore(self.application)

    def _real_initialize(self,app):
        self.__app = app

        self.__appid_ignore._real_initialize(app)

        if self.application.config.has_option('steam','libraries'):
            for libpath in self.application.config.get_string_list('steam','libraries'):
                self.add_library(libpath)
        self.__save_slot = self.application.config.connect('save',self._on_save)
            
    @GObject.Property
    def application(self):
        return self.__app
    
    @GObject.Property(list)
    def libraries(self):
        return self.__libraries
    
    @GObject.Property
    def appid_ignore(self):
        return self.__appid_ignore
    
    @GObject.Property
    def ignore_appids(self):
        return self.__appid_ignore.appids
    
    @GObject.Property
    def apps(self):
        steamapps={}
        for l in self.libraries:
            for k,v in l.apps.items():
                value={'lib':l,'acf':v,'game':None}
                if k in self.application.games.steam_items:
                    value['game']=self.application.games.steam_items[k]
                steamapps[k]=value

        return steamapps
    
    def add_library(self,lib):
        if isinstance(lib,str):
            sl = SteamLib(self.application,lib)
        elif isinstance(lib,SteamLib):
            sl = lib
        else:
            raise TypeError("lib is not a \"SteamLib\"-instance or a valid library path!")
        
        if sl.is_valid:
            for path in (i.path for i in self.__libraries):
                if path == sl.path:
                    return
                
            self.__libraries.append(sl)

    def remove_library(self,lib):
        if isinstance(lib,SteamLib) and lib in self.libraries:
            for i in range(len(self.__libraries)):
                if self.__libraries[i] == lib:
                    self.__libraries[i].destroy()
                    del self.__libraries[i]
                    return
        elif isinstance(lib,str):
            for i in range(len(self.__libraries)):
                if self.__libraries[i].path == lib:
                    self.__libraries[i].destroy()
                    del self.__libraries[i]
                    return


    def update_games(self,update_name=False):
        games = {}
        for lib in self.libraries:
            for appid,acf in lib.registered_apps.items():
                try:
                    g = self.application.steam_games[appid]
                    games[g.game_id] = {'appid':appid,'game':g,'acf':acf,'library':lib}
                except:
                    pass
        
        for gid,spec in games.items():
            game = spec['game']
            acf = spec['acf']
            appid = spec['appid']
            library = spec['lib']

            if acf['appid'] != appid:
                print("WARNING: Steam appid of game \"{game}\" does not match!".format(game=acf['name']),file=sys.stderr)

            if update_name:
                game.game_name = acf['name']

            game.installdir = os.path.join(library.path,'steamapps','common',acf['installdir'])
            game.save()

    @GObject.Property
    def unregistered_apps(self):
        apps = {}
        for lib in self.libraries:
            for appid,acf in lib.unregistered_apps.items():
                apps[appid] = {'acf':acf,'library':lib}
        return dict(sorted(apps.items()))
    
    def destroy(self):
        self.emit('destroy')

    def do_destroy(self):
        self.__appid_ignore.destroy()
        while len(self.__libraries) > 0:
            self.__libraries[-1].destroy()
            del self.__libraries[-1]

        self.application.config.diconnect('save',self.__save_slot)
        self.__app = None

    def _on_save(self,config):
        libs = [sl.path for sl in self.libraries]
        libs.sort()
        config.keyfile.set_string_list("steam","libraries",libs)
