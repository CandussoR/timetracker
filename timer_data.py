INSERT_TIMER_BEGINNING = '''INSERT INTO timer_data (task_id, date, time_beginning) 
                            VALUES (?,date(?),time(?))'''

UPDATE_TIMER_ENDING = '''UPDATE timer_data 
                        SET time_ending=(time(?)) 
                        WHERE time_ending IS NULL;'''

ADD_TIME_DIFFERENCE = '''UPDATE timer_data
                         SET time_elapsed = strftime('%s',time_ending) - strftime('%s',time_beginning)
                         WHERE time_elapsed IS NULL;'''

LAST_TIME_ELAPSED = '''SELECT time_elapsed 
                    FROM tablename 
                    ORDER BY column DESC 
                    LIMIT 1;'''

TIME_ELAPSED_PLUS_ONE_DAY = '''UPDATE timer_data
                         SET time_elapsed = time_elapsed + 86400
                         WHERE time_elapsed < 0;'''


def insert_beginning(connexion, task_at_hand_id, date, beginning_time):
    with connexion:
        connexion.execute(INSERT_TIMER_BEGINNING, (task_at_hand_id, date,\
                                beginning_time))

def update_ending(connexion, time_ending):
    with connexion:
        connexion.execute(UPDATE_TIMER_ENDING, [time_ending])

def add_elapsed_time(connexion):
    with connexion:
        connexion.execute(ADD_TIME_DIFFERENCE)

def time_elapsed_is_negative(connexion):
    with connexion:
        time_elapsed = connexion.execute(LAST_TIME_ELAPSED)
        return time_elapsed[0] < 0 

def add_day_to_time_elapsed(connexion):
    with connexion:
        connexion.execute(TIME_ELAPSED_PLUS_ONE_DAY)

def updating_row(connexion, time):
    update_ending(connexion, time)
    add_elapsed_time(connexion)
    if time_elapsed_is_negative(connexion) :
        add_day_to_time_elapsed(connexion)
