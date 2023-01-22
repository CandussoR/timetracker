from sqlite3.dbapi2 import Connection

INSERT_TIMER_BEGINNING = '''INSERT INTO timer_data (task_id, date, time_beginning) 
                            VALUES (?,date(?),time(?));'''

UPDATE_TIMER_ENDING = '''UPDATE timer_data 
                        SET time_ending=(time(?)) 
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

INSERT_PAST_TIMER = '''INSERT INTO timer_data (task_id, date, time_beginning, time_ending)
                    VALUES (?,date(?),time(?),time(?));'''

def insert_beginning(connexion : Connection, task_at_hand_id, date, beginning_time):
    with connexion:
        connexion.execute(INSERT_TIMER_BEGINNING, (task_at_hand_id, date,\
                                beginning_time))

def insert_old_timer(connexion : Connection, params):
    with connexion:
        connexion.execute(INSERT_PAST_TIMER, [*params])
    last_id = connexion.execute(LAST_ID).fetchone()[0] 
    update_time_elapsed(connexion, last_id)

def update_row_at_ending(connexion : Connection, time):
    last_id = connexion.execute(LAST_ID).fetchone()[0] 
    add_time_ending(connexion, time, last_id)
    update_time_elapsed(connexion, last_id)

def update_time_elapsed(connexion : Connection, id : int):
    add_elapsed_time(connexion, id)
    if time_elapsed_is_negative(connexion) :
        add_day_to_time_elapsed(connexion)

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
