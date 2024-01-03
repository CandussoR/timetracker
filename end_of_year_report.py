# .headers on
# .mode column/list
# .separator "|" / .separator ","

import sqlite_db as db
from sqlite3 import Connection
from timer_stats import task_list
# from matplotlib.pyplot import pie, show, title
# from numpy import array

# DAYS_IN_YEAR = "SELECT JULIANDAY(date('now', 'start of year', '+1 year')) - JULIANDAY(date('now', 'start of year'))"
# EXACT_TRIMESTER = {DAYS_IN_YEAR} / 4 

# DAYS_IN_YEAR = "SELECT JULIANDAY(date('now', 'start of year', '+1 year')) - JULIANDAY(date('now', 'start of year'))"
# EXACT_TRIMESTER = {DAYS_IN_YEAR} / 4 

# TIMER_DATA = '''
#     SELECT task_name, date, time_elapsed
#     FROM timer_data
#     JOIN tasks t ON t.id = timer_data.task_id AND t.task_name = (?)
#     WHERE date(strftime('%Y', date)) = date(strftime('%Y', 'now', '-1 year')) 
#     '''

# MID_YEAR = '''
#     SELECT task_name, date, time_elapsed
#     FROM timer_data
#     JOIN tasks t ON t.id = timer_data.task_id AND t.task_name = (?)
#     WHERE date(strftime('%Y', date)) = date(strftime('%Y', 'now')) 
# '''

# MID_YEAR_TO_Q3 = '''
#     SELECT task_name, date, time_elapsed
#     FROM timer_data
#     JOIN tasks t ON t.id = timer_data.task_id AND t.task_name = (?)
#     WHERE  date(strftime('%Y-%m-%d', date)) BETWEEN '2023-01-01' AND '2023-09-30' 
# '''

# LAST_YEAR_MID_YEAR = '''
#     SELECT task_name, date, time_elapsed
#     FROM timer_data
#     JOIN tasks t ON t.id = timer_data.task_id AND t.task_name = (?)
#     WHERE date(strftime('%Y-%m-%d', date)) BETWEEN '2022-01-01' AND date(strftime('%Y-%m-%d', 'now', '-1 year')) 
# '''
# YEARLY_REPORT = f'''
#     WITH td as (
#         {MID_YEAR_TO_Q3}
#     ),
#     total_time as (
#         SELECT task_name, sum(time_elapsed) as totsec
#         FROM td
#     )
#     SELECT td.task_name, 
#            COUNT(DISTINCT date) as days_done,
#            printf("%02d:%02d:%02d:%02d",
#                   totsec / 86400, 
#                   (totsec % 86400) / 3600,
#                   (totsec % 3600) / 60,
#                   (totsec % 86400) / 3600) as total,
#             tt.totsec
#     FROM td
#     JOIN total_time tt ON td.task_name = tt.task_name
# '''

# Create a calendar and joins timer_data : shows not-worked day as well as worked.
MEAN_TIME_WORKED_AND_UNWORKED = '''WITH RECURSIVE dates(day,date) AS ( 
    VALUES(strftime('%w', '2023-01-01'), '2023-01-01') 
    UNION ALL 
    SELECT strftime('%w', DATE(date, '+1 day')), DATE(date, '+1 day') 
    FROM dates 
    WHERE date < '2023-12-31'
    ), ad AS ( 
        SELECT 
            d.day, 
            d.date, 
            time_elapsed, 
            SUM(t.time_elapsed) OVER (PARTITION BY d.date) as total_time, 
            ROW_NUMBER() OVER (PARTITION BY d.date) as row_num 
        FROM 
            dates d 
        LEFT JOIN 
            timer_data t ON t.date = d.date 
    ), total_time_all_day AS ( 
        SELECT 
            day, 
            date, 
            total_time, 
            COALESCE(total_time,0) as all_total 
        FROM ad 
        WHERE row_num = 1 
    ), avg_time_all_day AS (
        SELECT 
            DISTINCT day, 
            AVG(total_time) OVER (PARTITION BY day) as avg_worked, 
            AVG(all_total) OVER (PARTITION BY day) as avg_unworked 
        FROM total_time_all_day) 
    SELECT 
        day, 
        ROUND(avg_worked, 2) as avg_worked, 
        ROUND(avg_unworked, 2) as avg_unworked 
    FROM avg_time_all_day;
    '''

def format_time(time : float | int) -> str:
    return '{:02d}:{:02d}:{:02d}'.format(int((time % 86400) // 3600), int((time % 3600) // 60),int(time % 60) )

# task_array = []
# days_count_array = []
# for task in task_list(connexion) :
#     task_name, days_done_count, total_time = connexion.execute(YEARLY_REPORT, [task[0]]).fetchone()
#     task_array.append(task_name)
#     days_count_array.append(int(days_done_count))
#     if days_done_count > 10:
#         print(f"{task_name} | {days_done_count} | {total_time}\n")

#TODO: extract data into a file
#TODO: decide what the file should be, what the separators should be

#TODO: voir pour chaque jour la portion du temps dédié à telle tâche.
if __name__ == '__main__':
    connexion = db.connect('timer_data.db')
    stats = connexion.execute(MEAN_TIME_WORKED_AND_UNWORKED).fetchall()
    ordered = []
    ordered.extend(stats[1:])
    ordered.append(stats[0])
    ordered_formatted = [(day, format_time(avg_worked), format_time(avg_unworked)) for day, avg_worked, avg_unworked in ordered]
    print(ordered_formatted)