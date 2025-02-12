import sqlite3

CREATE_TASK_TABLE = """
      CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
      task_name TEXT NOT NULL,
      subtask TEXT,
      guid TEXT UNIQUE NOT NULL,
      UNIQUE (task_name, subtask));
      """

CREATE_TAGS_TABLE = """
    CREATE TABLE IF NOT EXISTS tags (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    tag TEXT NOT NULL UNIQUE,
    guid TEXT UNIQUE NOT NULL
    );
    """

CREATE_TIMER_TABLE = """
    CREATE TABLE IF NOT EXISTS timer_data (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    date REAL,
    time_beginning REAL,
    time_ending REAL,
    time_elapsed REAL,
    tag_id INTEGER,
    log TEXT,
    guid TEXT UNIQUE NOT NULL,
    FOREIGN KEY (task_id)
        REFERENCES tasks (id),
    FOREIGN KEY (tag_id)
        REFERENCES tags (id)
        );

    CREATE INDEX IF NOT EXISTS idx_date_timer ON timer_data (date);
    CREATE INDEX IF NOT EXISTS idx_task_id_timer ON timer_data (task_id);
    CREATE INDEX IF NOT EXISTS idx_tag_id_timer ON timer_data (tag_id);
    """

# CREATE_TEMP_TASK_TABLE = """
#     CREATE TABLE IF NOT EXISTS tmp_tasks (
#       id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
#       task_name TEXT NOT NULL,
#       subtask TEXT,
#       guid TEXT UNIQUE NOT NULL,
#       UNIQUE (task_name, subtask));
#     """

# CREATE_TEMP_TAGS_TABLE = """
#     CREATE TABLE IF NOT EXISTS tmp_tags (
#     id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
#     tag TEXT NOT NULL UNIQUE,
#     guid TEXT UNIQUE NOT NULL
#     );
#     """

# CREATE_TEMP_TIMER_TABLE = """
#     CREATE TABLE IF NOT EXISTS tmp_timer_data(
#     id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
#     task_id INTEGER NOT NULL,
#     date REAL,
#     time_beginning REAL,
#     time_ending REAL,
#     time_elapsed REAL,
#     tag_id INTEGER,
#     log TEXT,
#     guid TEXT UNIQUE NOT NULL,
#     FOREIGN KEY (task_id)
#         REFERENCES tasks (id),
#     FOREIGN KEY (tag_id)
#         REFERENCES tags (id)
#         );
# """


def connect(db):
    connexion = sqlite3.connect(db)
    # Adds the foreign key constraint on the sqlite db to insure data integrity.
    connexion.execute('PRAGMA foreign_keys = on;')
    return connexion


def create_tables(connexion):
    with connexion:
        connexion.execute(CREATE_TASK_TABLE)
        connexion.execute(CREATE_TAGS_TABLE)
        connexion.executescript(CREATE_TIMER_TABLE)

        # connexion.execute(CREATE_TEMP_TASK_TABLE)
        # connexion.execute(CREATE_TEMP_TAGS_TABLE)
        # connexion.execute(CREATE_TEMP_TIMER_TABLE)