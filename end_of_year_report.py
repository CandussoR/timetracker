# .headers on
# .mode column/list
# .separator "|" / .separator ","

import sqlite_db as db
from sqlite3 import Connection
from timer_stats import task_list
# from matplotlib.pyplot import pie, show, title
# from numpy import array

connexion = db.connect('timer_data.db')

DAYS_IN_YEAR = "SELECT JULIANDAY(date('now', 'start of year', '+1 year')) - JULIANDAY(date('now', 'start of year'))"
EXACT_TRIMESTER = {DAYS_IN_YEAR} / 4 

DAYS_IN_YEAR = "SELECT JULIANDAY(date('now', 'start of year', '+1 year')) - JULIANDAY(date('now', 'start of year'))"
EXACT_TRIMESTER = {DAYS_IN_YEAR} / 4 

TIMER_DATA = '''
    SELECT task_name, date, time_elapsed
    FROM timer_data
    JOIN tasks t ON t.id = timer_data.task_id AND t.task_name = (?)
    WHERE date(strftime('%Y', date)) = date(strftime('%Y', 'now', '-1 year')) 
    '''

MID_YEAR = '''
    SELECT task_name, date, time_elapsed
    FROM timer_data
    JOIN tasks t ON t.id = timer_data.task_id AND t.task_name = (?)
    WHERE date(strftime('%Y', date)) = date(strftime('%Y', 'now')) 
'''

MID_YEAR_TO_Q3 = '''
    SELECT task_name, date, time_elapsed
    FROM timer_data
    JOIN tasks t ON t.id = timer_data.task_id AND t.task_name = (?)
    WHERE  date(strftime('%Y-%m-%d', date)) BETWEEN '2023-01-01' AND '2023-09-30' 
'''

LAST_YEAR_MID_YEAR = '''
    SELECT task_name, date, time_elapsed
    FROM timer_data
    JOIN tasks t ON t.id = timer_data.task_id AND t.task_name = (?)
    WHERE date(strftime('%Y-%m-%d', date)) BETWEEN '2022-01-01' AND date(strftime('%Y-%m-%d', 'now', '-1 year')) 
'''
YEARLY_REPORT = f'''
    WITH td as (
        {MID_YEAR_TO_Q3}
    ),
    total_time as (
        SELECT task_name, sum(time_elapsed) as totsec
        FROM td
    )
    SELECT td.task_name, 
           COUNT(DISTINCT date) as days_done,
           printf("%02d:%02d:%02d:%02d",
                  totsec / 86400, 
                  (totsec % 86400) / 3600,
                  (totsec % 3600) / 60,
                  (totsec % 86400) / 3600) as total,
            tt.totsec
    FROM td
    JOIN total_time tt ON td.task_name = tt.task_name
'''

task_array = []
days_count_array = []
for task in task_list(connexion) :
    task_name, days_done_count, total_time = connexion.execute(YEARLY_REPORT, [task[0]]).fetchone()
    task_array.append(task_name)
    days_count_array.append(int(days_done_count))
    if days_done_count > 10:
        print(f"{task_name} | {days_done_count} | {total_time}\n")

#TODO: extract data into a file
#TODO: decide what the file should be, what the separators should be

#TODO: voir pour chaque jour la portion du temps dédié à telle tâche.
if __name__ == '__main__':
    pass