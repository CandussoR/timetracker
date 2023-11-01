from datetime import datetime
from sqlite3.dbapi2 import Connection

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
                         WHERE time_elapsed < 0;'''

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
def insert_beginning(connexion : Connection, task_at_hand_id : str, date : datetime, beginning_time : datetime, tag_id : str) -> int:
    with connexion:
        if tag_id:
            return connexion.execute(INSERT_TIMER_BEGINNING_WITH_TAG, (task_at_hand_id, date,\
                                beginning_time, tag_id)).lastrowid
        else:
            return connexion.execute(INSERT_TIMER_BEGINNING, (task_at_hand_id, date,\
                                beginning_time)).lastrowid

def insert_old_timer(connexion : Connection, id, date, time_beginning, time_ending, tag_id, log):
    with connexion:
        if tag_id and (log != ""):
            last_id = connexion.execute(INSERT_PAST_TIMER_WITH_TAG_AND_LOG, [id, date, time_beginning, time_ending, tag_id, log]).lastrowid
        elif tag_id and (log == ""):
            last_id = connexion.execute(INSERT_PAST_TIMER_WITH_TAG_ONLY, [id, date, time_beginning, time_ending, tag_id]).lastrowid
        elif (not tag_id) and log:
            last_id = connexion.execute(INSERT_PAST_TIMER_WITH_LOG_ONLY, [id, date, time_beginning, time_ending, log]).lastrowid
        else:
            last_id = connexion.execute(INSERT_PAST_TIMER_WITHOUT_TAG_OR_LOG, [id, date, time_beginning, time_ending]).lastrowid
    # last_id = connexion.execute(LAST_ID).fetchone()[0] 
    update_time_elapsed(connexion, last_id)

def update_row_at_ending(connexion : Connection, time : datetime,  last_id : int | None = None, log : str = ""):
    if not last_id:
        last_id = connexion.execute(LAST_ID).fetchone()[0]
    if log == "":
        add_time_ending(connexion, time, last_id)
    else :
        update_time_and_log(connexion, time, log, last_id)
    update_time_elapsed(connexion, last_id)

def update_time_elapsed(connexion : Connection, id : int):
    add_elapsed_time(connexion, id)
    if time_elapsed_is_negative(connexion) :
        add_day_to_time_elapsed(connexion)

def update_time_and_log(connexion, time, log, id):
    with connexion:
        connexion.execute(UPDATE_TIMER_ENDING_AND_LOG, [time, log, id])

def add_time_ending(connexion : Connection, time_ending, id):
    with connexion:
        connexion.execute(UPDATE_TIMER_ENDING, [time_ending, id])

def add_elapsed_time(connexion : Connection, id : int):
    with connexion:
        connexion.execute(ADD_TIME_DIFFERENCE, [id])

def time_elapsed_is_negative(connexion : Connection):
    with connexion:
        return connexion.execute(LAST_TIME_ELAPSED).fetchone()[1] < 0

def add_day_to_time_elapsed(connexion : Connection):
    with connexion:
        connexion.execute(TIME_ELAPSED_PLUS_ONE_DAY)
