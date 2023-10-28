import sqlite3

CREATE_TASK_TABLE = '''
      CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
      task_name TEXT NOT NULL,
      subtask TEXT,
      UNIQUE (task_name, subtask));
      '''

CREATE_TAGS_TABLE = '''
    CREATE TABLE IF NOT EXISTS tags (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    tag TEXT NOT NULL UNIQUE
    );
    '''

CREATE_TIMER_TABLE = '''
    CREATE TABLE IF NOT EXISTS timer_data(
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    date REAL,
    time_beginning REAL,
    time_ending REAL,
    time_elapsed REAL,
    tag_id INTEGER,
    log TEXT,
    FOREIGN KEY (task_id)
        REFERENCES tasks (id),
    FOREIGN KEY (tag_id)
        REFERENCES tags (id)
        );
    '''

def connect(db):
    return sqlite3.connect(db)

def create_tables(connexion):
    with connexion:
        connexion.execute(CREATE_TASK_TABLE)
        connexion.execute(CREATE_TAGS_TABLE)
        connexion.execute(CREATE_TIMER_TABLE)