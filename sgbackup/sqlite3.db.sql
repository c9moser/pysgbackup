CREATE TABLE games (
    id INTEGER PRIMARY KEY,
    game_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(512) UNIQUE NOT NULL,
    savegame_name VARCHAR(256),
    savegame_root VARCHAR(512) NOT NULL,
    savegame_dir VARCHAR(512) NOT NULL,
    final_backup CHAR(1) DEFAULT 'N',
    steam_appid VARCHAR(128)
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

CREATE TABLE plugins (
    id INTEGER PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    version VARCHAR(32) DEFAULT '0.0.0',
    enabled CHAR(1) DEFAULT 'N'
);
CREATE INDEX plugins_name_index ON plugins(name);

CREATE TABLE filelist (
    id INTEGER PRIMARY KEY,
    game INTEGER NOT NULL,
    filename VARCHAR(512) UNIQUE NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    hash VARCHAR(256) DEFAULT '',
    ftp_transferred CHAR[1] DEFAULT 'N',
    FOREIGN KEY (game) REFERENCES games(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);
CREATE INDEX filelist_game_index ON filelist(game);
CREATE INDEX filelist_filename_index ON filelist(filename);

CREATE TABLE filelist_extrafiles (
    id INTEGER PRIMARY KEY,
    file INTEGER NOT NULL,
    filename VARCHAR(512) UNIQUE NOT NULL,
    use_ftp CHAR(1) DEFAULT 'N',
    ftp_transferred CHAR(1) DEFAULT 'N',
    
    FOREIGN KEY (file) REFERENCES filelist(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE steamapp_ignore (
    id INTEGER PRIMARY KEY,
    steam_appid VARCHAR(128) UNIQUE NOT NULL
);
CREATE INDEX steamapp_ignore_steam_appid ON steamapp_ignore(steam_appid);

