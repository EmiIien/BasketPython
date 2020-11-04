CREATE TABLE user (
    id_user INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    pswrd TEXT NOT NULL,
    mail TEXT,
    age INTEGER NOT NULL,
    
);

CREATE TABLE game (
    id_game INTEGER PRIMARY KEY AUTOINCREMENT,
    game_title TEXT NOT NULL,
    adress TEXT NOT NULL,
    game_day DATE NOT NULL,
    age_Max INT,
    age_MIN INT,
    
);

CREATE TABLE player (
    id_user INTEGER NOT NULL,
    id_game INTEGER NOT NULL,
    FOREIGN KEY (id_user) REFERENCES user(id_user),
    FOREIGN KEY (id_game) REFERENCES game(id_game),

);