import sqlite3

CREATE_TASK_TABLE = '''
      CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
      task_name TEXT NOT NULL,
      subtask TEXT,
      UNIQUE (task_name, subtask));
      '''

CREATE_TIMER_TABLE = '''
    CREATE TABLE IF NOT EXISTS timer_data(
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    date REAL,
    time_beginning REAL,
    time_ending REAL,
    time_elapsed REAL,
    FOREIGN KEY (task_id)
        REFERENCES tasks (id)
        );
    '''

def connect(db):
    return sqlite3.connect(db)

def create_tables(connexion):
    with connexion:
        connexion.execute(CREATE_TIMER_TABLE)
        connexion.execute(CREATE_TASK_TABLE)