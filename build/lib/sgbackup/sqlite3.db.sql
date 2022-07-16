CREATE TABLE games (
    id INTEGER PRIMARY KEY,
    game_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(512) UNIQUE NOT NULL,
    savegame_name VARCHAR(256),
    savegame_root VARCHAR(512) NOT NULL,
    final_backup CHAR(1) DEFAULT 'N'
);
CREATE INDEX games_game_id_index ON games(game_id);
CREATE INDEX games_savegame_name ON games(savegame_name);

CREATE TABLE game_variables (
    id INTEGER PRIMARY KEY,
    game INTEGER NOT NULL,
    name VARCHAR(512) NOT NULL,
    value TEXT DEFAULT '',
    
    UNIQUE (game,name),
    
    FOREIGN KEY (game) REFERENCES games(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);
CREATE INDEX game_variables_game_index ON game_variables(game);
CREATE INDEX game_variables_name_index ON game_variables(name);


CREATE TABLE gameconf (
    id INTEGER PRIMARY KEY,
    game INTEGER NOT NULL,
    filename VARCHAR(1024) UNIQUE NOT NULL,
    checksum CHAR(32) NOT NULL,    
    user_file CHAR(1) DEFAULT 'N',
    
    UNIQUE(game,filename),
    
    FOREIGN KEY (game) REFERENCES games(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);
CREATE INDEX gameconf_game_index ON gameconf(game);
CREATE INDEX gameconf_filename_index ON gameconf(filename);

