CREATE TABLE games (
    id INTEGER PRIMARY KEY
    game_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(512) UNIQUE NOT NULL,
    savegame_name VARCHAR(256),
    savegame_root VARCHAR(512) NOT NULL,
    savegame_dir VARCHAR(512) NOT NULL,
    final_backup CHAR(1) DEFAULT 'N'
);

CREATE TABLE games_conf (
    id INTEGER PRIMARY KEY
    game INTEGER NOT NULL,
    filename VARCHAR(1024) UNIQUE NOT NULL,
    chksum CHAR(32) NOT NULL,    
    user_file CHAR(1) DEFAULT 'N',
    
    UNIQUE(game,filename),
    
    FOREIGN KEY (game) REFERENCES games(id)
        ON_UPDATE CASCADE
        ON_DELETE CASCADE
);

CREATE INDEX games_game_id_index ON games(game_id);
CREATE INDEX games_savegame_name ON games(savegame_name);

