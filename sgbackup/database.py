import config
import sqlite3

class Database:
    DB_ENGINE="sqlite3"
        
    def __init__(self,db=None, connect=True):
        self.__db = None
        
        if (connect):
            if not db:
                self._connect(config.CONFIG["sg-database"]);
            else
                self._connect(db)
        
        
    def _connect(self,db):
        self.__db = __self.connect(db)
        
    def connect_user_db(self,db):
        pass
        
    def close(self):
        if self.DB_ENGINE == "sqlite3" and self.__db:
            self.__db.close()
            self.__db = None
            
    def _init_db(self):
        pass

def main():
    pass
    
if __name__ == '__main__':
    main()


