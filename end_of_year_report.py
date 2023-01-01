# .headers on
# .mode column/list
# .separator "|" / .separator ","

import sqlite_db as db
from timer_stats import task_list

connexion = db.connect('timer_data.db')

TIMER_DATA = '''
    SELECT task_name, date, time_elapsed
    FROM timer_data
    JOIN tasks t ON t.id = timer_data.task_id AND t.task_name = (?)
    WHERE date(strftime('%Y', date)) = date(strftime('%Y', 'now', '-1 year')) 
    '''

YEARLY_REPORT = f'''
    WITH td as (
        {TIMER_DATA}
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
                  (totsec % 86400) / 3600) as total
    FROM td
    JOIN total_time tt ON td.task_name = tt.task_name
'''

for task in task_list(connexion) :
    task_name, days_done_count, total_time = connexion.execute(YEARLY_REPORT, [task[0]]).fetchone()
    if days_done_count > 10:
        print(f"{task_name} | {days_done_count} | {total_time}\n")

#TODO: extract data into a file
#TODO: decide what the file should be, what the separators should be