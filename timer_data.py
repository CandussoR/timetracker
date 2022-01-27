INSERT_TIMER_BEGINNING = 'INSERT INTO timer_data (task_id, date, time_beginning) VALUES (?,date(?),time(?))'

UPDATE_TIMER_ENDING = 'UPDATE timer_data SET time_ending=(time(?)) WHERE time_ending IS NULL;'

TIME_DIFFERENCE = '''SELECT strftime('%s',time_ending) - strftime('%s',time_beginning)
                     FROM timer_data WHERE time_elapsed IS NULL;'''

ADD_TIME_DIFFERENCE = '''UPDATE timer_data SET time_elapsed = time(?, 'unixepoch')
                         WHERE time_elapsed IS NULL;'''

def insert_beginning(connexion, task_at_hand_id, date, beginning_time):
    with connexion:
        connexion.execute(INSERT_TIMER_BEGINNING, (task_at_hand_id, date,\
                                beginning_time))

def update_ending(connexion, time_ending):
    with connexion:
        connexion.execute(UPDATE_TIMER_ENDING, [time_ending])

def time_difference(connexion):
    with connexion:
        time_difference = connexion.execute(TIME_DIFFERENCE).fetchone()
        return time_difference[0]

def add_elapsed_time(connexion):
    time_elapsed = time_difference(connexion)
    with connexion:
        connexion.execute(ADD_TIME_DIFFERENCE, [time_elapsed])

def updating_row(connexion, time):
    update_ending(connexion, time)
    add_elapsed_time(connexion)
