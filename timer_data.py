INSERT_TIMER_BEGINNING = '''INSERT INTO timer_data (task_id, date, time_beginning) 
                            VALUES (?,date(?),time(?));'''

UPDATE_TIMER_ENDING = '''UPDATE timer_data 
                        SET time_ending=(time(?)) 
                        WHERE time_ending IS NULL;'''

ADD_TIME_DIFFERENCE = '''UPDATE timer_data
                         SET time_elapsed = strftime('%s',time_ending) - strftime('%s',time_beginning)
                         WHERE time_elapsed IS NULL;'''

LAST_TIME_ELAPSED = '''SELECT id, time_elapsed 
                    FROM timer_data 
                    ORDER BY id DESC 
                    LIMIT 1;'''

TIME_ELAPSED_PLUS_ONE_DAY = '''UPDATE timer_data
                         SET time_elapsed = time_elapsed + 86400
                         WHERE time_elapsed < 0;'''

INSERT_PAST_TIMER = '''INSERT INTO timer_data (task_id, date, time_beginning, time_ending)
                    VALUES (?,date(?),time(?),time(?));'''

def insert_beginning(connexion, task_at_hand_id, date, beginning_time):
    with connexion:
        connexion.execute(INSERT_TIMER_BEGINNING, (task_at_hand_id, date,\
                                beginning_time))

def insert_old_timer(connexion, params):
    with connexion:
        connexion.execute(INSERT_PAST_TIMER, [*params])
    update_time_elapsed(connexion)

def update_row_at_ending(connexion, time):
    add_time_ending(connexion, time)
    update_time_elapsed(connexion)

def update_time_elapsed(connexion):
    add_elapsed_time(connexion)
    if time_elapsed_is_negative(connexion) :
        add_day_to_time_elapsed(connexion)

def add_time_ending(connexion, time_ending):
        with connexion:
                connexion.execute(UPDATE_TIMER_ENDING, [time_ending])

def add_elapsed_time(connexion):
        with connexion:
                connexion.execute(ADD_TIME_DIFFERENCE)

def time_elapsed_is_negative(connexion):
        with connexion:
                time_elapsed = connexion.execute(LAST_TIME_ELAPSED).fetchone()
                return time_elapsed[1] < 0 

def add_day_to_time_elapsed(connexion):
        with connexion:
                connexion.execute(TIME_ELAPSED_PLUS_ONE_DAY)

    