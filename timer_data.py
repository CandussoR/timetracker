from dataclasses import dataclass
from datetime import datetime
from sqlite3.dbapi2 import Connection

@dataclass
class TimeRecord():
    id : int | str = None
    task_id : int | str = None
    date : datetime = None
    time_beginning : datetime = None
    time_ending : datetime = None
    time_elapsed : int = None
    tag_id : int | str = None
    log : str = None
    
INSERT_TIMER_BEGINNING = '''INSERT INTO timer_data (task_id, date, time_beginning) 
                            VALUES (?,date(?),time(?))
                            RETURNING id;'''

INSERT_TIMER_BEGINNING_WITH_TAG = '''INSERT INTO timer_data (task_id, date, time_beginning, tag_id) 
                            VALUES (?,date(?),time(?),?)
                            RETURNING id;'''

UPDATE_TIMER_ENDING = '''UPDATE timer_data 
                        SET time_ending=(time(?))
                        WHERE id = (?);'''

UPDATE_TIMER_ENDING_AND_LOG = '''UPDATE timer_data 
                        SET time_ending=(time(?)), log=(?)
                        WHERE id = (?);'''

LAST_ID = 'SELECT id FROM timer_data ORDER BY id DESC LIMIT 1;'

ADD_TIME_DIFFERENCE = '''UPDATE timer_data
                         SET time_elapsed = strftime('%s',time_ending) - strftime('%s',time_beginning)
                         WHERE id = (?);'''

LAST_TIME_ELAPSED = '''SELECT id, time_elapsed 
                    FROM timer_data 
                    ORDER BY id DESC 
                    LIMIT 1;'''

TIME_ELAPSED_PLUS_ONE_DAY = '''UPDATE timer_data
                         SET time_elapsed = time_elapsed + 86400
                         WHERE id=(?);'''

INSERT_PAST_TIMER_WITHOUT_TAG_OR_LOG = '''INSERT INTO timer_data (task_id, date, time_beginning, time_ending)
                    VALUES (?,date(?),time(?),time(?))
                    RETURNING id;'''

INSERT_PAST_TIMER_WITH_TAG_ONLY = '''INSERT INTO timer_data (task_id, date, time_beginning, time_ending, tag_id)
                    VALUES (?,date(?),time(?),time(?),?)
                    RETURNING id;'''

INSERT_PAST_TIMER_WITH_LOG_ONLY = '''INSERT INTO timer_data (task_id, date, time_beginning, time_ending, log)
                    VALUES (?,date(?),time(?),time(?), ?)
                    RETURNING id;'''

INSERT_PAST_TIMER_WITH_TAG_AND_LOG = '''INSERT INTO timer_data (task_id, date, time_beginning, time_ending, tag_id, log)
                    VALUES (?,date(?),time(?),time(?),?,?)
                    RETURNING id;'''

def insert_beginning(connexion : Connection, record: TimeRecord) -> int:
    with connexion:
        if record.tag_id:
            return connexion.execute(INSERT_TIMER_BEGINNING_WITH_TAG, 
                                     (record.task_id, record.date, record.time_beginning, record.tag_id)
                                     ).lastrowid
        else:
            return connexion.execute(INSERT_TIMER_BEGINNING,
                                     (record.task_id, record.date, record.time_beginning)
                                     ).lastrowid
            

def insert_old_timer(connexion : Connection, record : TimeRecord):
    with connexion:
        if record.tag_id and record.log:
            record.id = connexion.execute(INSERT_PAST_TIMER_WITH_TAG_AND_LOG, 
                                          [record.task_id, record.date, record.time_beginning, record.time_ending, record.tag_id, record.log]
                                          ).lastrowid
        elif record.tag_id and not record.log:
            record.id = connexion.execute(INSERT_PAST_TIMER_WITH_TAG_ONLY, 
                                          [record.task_id, record.date, record.time_beginning, record.time_ending, record.tag_id]
                                          ).lastrowid
        elif (not record.tag_id) and record.log:
            record.id = connexion.execute(INSERT_PAST_TIMER_WITH_LOG_ONLY, 
                                          [record.task_id, record.date, record.time_beginning, record.time_ending, record.log]
                                          ).lastrowid
        else:
            record.id = connexion.execute(INSERT_PAST_TIMER_WITHOUT_TAG_OR_LOG, 
                                          [record.task_id, record.date, record.time_beginning, record.time_ending]
                                          ).lastrowid
    update_time_elapsed(connexion, record)

def update_row_at_ending(connexion : Connection, record : TimeRecord):
    if not record.log:
        add_time_ending(connexion, record)
    else :
        add_time_ending_and_log(connexion, record)
    update_time_elapsed(connexion, record)

def update_last_row_ending(connexion : Connection, time : datetime):
    row = list(connexion.execute("SELECT * FROM timer_data ORDER BY id DESC LIMIT 1").fetchone())
    record = TimeRecord(*row)
    with connexion:
        connexion.execute(UPDATE_TIMER_ENDING, [time, record.id])
        update_time_elapsed(connexion, record)

def update_time_elapsed(connexion : Connection, record : TimeRecord):
    record.time_elapsed = add_elapsed_time(connexion, record)
    if record.time_elapsed < 0:
        add_day_to_time_elapsed(connexion)

def add_time_ending_and_log(connexion, record : TimeRecord):
    with connexion:
        connexion.execute(UPDATE_TIMER_ENDING_AND_LOG, [record.time_ending, record.log, record.id])

def add_time_ending(connexion : Connection, record : TimeRecord):
    with connexion:
        record.time_ending = connexion.execute(UPDATE_TIMER_ENDING, [record.time_ending, record.id])

def add_elapsed_time(connexion : Connection, record : TimeRecord) -> int:
    with connexion:
        connexion.execute(ADD_TIME_DIFFERENCE, [record.id])
        return connexion.execute("SELECT time_elapsed FROM timer_data WHERE id=(?)", [record.id]).fetchone()[0]

def add_day_to_time_elapsed(connexion : Connection, record: TimeRecord):
    with connexion:
        connexion.execute(TIME_ELAPSED_PLUS_ONE_DAY, [record.id])
