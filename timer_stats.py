from typing import Tuple, Union
from sqlite3.dbapi2 import Connection
from datetime import datetime

TIME_PER_TASK_TODAY = '''SELECT t.task_name, time(sum(time_elapsed), 'unixepoch') as time
                   FROM timer_data td
                   JOIN tasks t ON t.id = td.task_id
                   WHERE date(date) = date('now')
                   GROUP BY t.task_name
                   ORDER BY time DESC;'''

TODAY_COUNT = "SELECT COUNT(*) FROM timer_data WHERE date(date) = date('now');"

TOTAL_TIME_TODAY = '''SELECT time(sum(time_elapsed), 'unixepoch') FROM timer_data
                      WHERE date(date) = date('now');'''

WEEK_COUNT = "SELECT COUNT(*) FROM timer_data WHERE date(date) > date('now', 'weekday 0', '-7 days')"

DATES = "SELECT date('now', 'weekday 1', ?), date('now', 'weekday 0', ?)"

SELECT_WEEK_TIMERS = '''
        SELECT *
        FROM timer_data
        WHERE date(date) BETWEEN date('now', 'weekday 0', ?) and date('now', 'weekday 1', ?);'''

TOTAL_TIME_THIS_WEEK = '''
    SELECT printf("%02d:%02d:%02d", totsec / 3600, (totsec % 3600) / 60, (totsec % 86400) / 3600) as total
    FROM (
        SELECT sum(time_elapsed) as totsec
        FROM timer_data
        WHERE date(date) > date('now', 'weekday 0', '-7 days')
        );'''

TOTAL_TIME_PARTICULAR_WEEK = '''
    SELECT printf("%02d:%02d:%02d", totsec / 3600, (totsec % 3600) / 60, (totsec % 86400) / 3600) as total
    FROM (
        SELECT sum(time_elapsed) as totsec
        FROM timer_data
        WHERE date BETWEEN date('now', 'weekday 1', ?) and date('now', 'weekday 0', ?)
        );'''

YEAR_COUNT = "SELECT COUNT(*) FROM timer_data WHERE date(strftime('%Y', date)) = date(strftime('%Y', 'now'))"

TOTAL_TIME_YEAR = '''
    SELECT printf("%02d:%02d:%02d:%02d",
                  totsec / 86400,
                  (totsec % 86400) / 3600,
                  (totsec % 3600) / 60,
                  (totsec % 86400) / 3600) as total
    FROM (
        SELECT sum(time_elapsed) as totsec
        FROM timer_data
        WHERE date(strftime('%Y', date)) = date(strftime('%Y', 'now'))
        );'''


DAY_MAX = '''SELECT date, MAX(sum_time)
            FROM (
            SELECT date, time(sum(time_elapsed), 'unixepoch') as sum_time
            FROM timer_data
            GROUP BY date);'''

AVG_TIME_ALL_DAYS = '''SELECT time(AVG(sum_time), 'unixepoch')
            FROM (
            SELECT sum(time_elapsed) as sum_time
            FROM timer_data
            );'''

AVG_TIME_DAY = '''SELECT time(AVG(sum_time), 'unixepoch')
            FROM (
            SELECT sum(time_elapsed) as sum_time
            FROM timer_data
            WHERE date LIKE (?)
            GROUP BY date
            );'''

MAX_AND_CURRENT_STREAK ='''
with cte AS (
    SELECT task_name, SUM(COALESCE(flag, 1)) OVER (PARTITION BY task_name ORDER BY date) grp
    FROM (
        SELECT t.task_name, date,
                date(date, '-1 day') <> lag(date) OVER (PARTITION BY t.task_name ORDER BY date) flag
        FROM timer_data
        JOIN tasks t ON t.id = timer_data.task_id
        WHERE task_name LIKE (?)
        GROUP BY date)
        )
SELECT MAX(COUNT(*)) OVER () longest_streak,
            COUNT(*) current_streak
FROM cte
GROUP BY grp
ORDER BY grp desc
LIMIT 1;
'''

TASK_LIST = 'SELECT DISTINCT task_name FROM tasks;'

def display_stats(connexion : Connection):
    # Count number of timers and total time for different spans (day, week, year),
    # gives an average time per day and a maximum.
    today_timer = timer_count(connexion, 'today')
    suffix = 's' if today_timer > 1 else ''
    print(f"Today : {today_timer} timer{suffix} ({total_time(connexion, 'today')}).")

    for task, time in time_per_task_today(connexion):
        task_streak = max_and_current_streaks(connexion, task)
        max = "(max streak!)" if task_streak[0][1] == task_streak[0][0] else f"(max : {task_streak[0][0]})"
        print(f"\t{task} : {time}")
        print(f"\t\tCurrent streak : {task_streak[0][1]} {max}")

    print(f"\nThis year's average day : {average_day_this_year(connexion)}")

    max_stat = max_in_a_day(connexion)
    print(f"\nYour maximum : {max_stat[1]} ({max_stat[0]}).\n")

    print(f"This week : { timer_count(connexion, 'week') } timer{suffix} ({ total_time(connexion, 'week') }).\n")

    print(f"This year : {timer_count(connexion, 'year')} timer{suffix} ({total_time(connexion, 'year')}).\n")

    more = input("See every task max streak (y) ?\n\t>> ")
    if more == 'y':
        all_task_streaks(connexion)

    weeks = input("See last weeks (y) ?\n\t>> ")
    if weeks == 'y':
        number_of_weeks : int = int(input("\tHow many ?\n\t>> "))
        past_weeks(connexion, number_of_weeks)

def timer_count(connexion : Connection, time_span : str) -> int :
    with connexion:
        if time_span == 'today':
            number = connexion.execute(TODAY_COUNT).fetchone()
        elif time_span == 'week':
            number = connexion.execute(WEEK_COUNT).fetchone()
        elif time_span == 'year':
            number = connexion.execute(YEAR_COUNT).fetchone()
    return number[0]

def total_time(connexion : Connection, time_span : str) -> str :
    with connexion:
        if time_span == 'today':
            timer_per_task = connexion.execute(TOTAL_TIME_TODAY).fetchone()
        elif time_span == 'week':
            timer_per_task = connexion.execute(TOTAL_TIME_THIS_WEEK).fetchone()
        elif time_span == 'year':
            timer_per_task = connexion.execute(TOTAL_TIME_YEAR).fetchone()
        return timer_per_task[0]

def time_per_task_today(connexion : Connection) -> str:
    with connexion:
        return connexion.execute(TIME_PER_TASK_TODAY).fetchall()

def max_in_a_day(connexion : Connection) -> Tuple[str, str]:
    with connexion:
        return connexion.execute(DAY_MAX).fetchone()

def all_time_average_day(connexion : Connection) -> str:
    with connexion:
        return connexion.execute(AVG_TIME_ALL_DAYS).fetchone()[0]

def average_day_this_year(connexion : Connection) -> str:
    with connexion:
        return connexion.execute(AVG_TIME_DAY, [f"{datetime.now().year}%"]).fetchone()[0]
        
def average_day_for_year(connexion : Connection, year : Union[str, int]) -> str:
    with connexion:
        return connexion.execute(AVG_TIME_DAY, [f"{str(year)}%"]).fetchone()[0]

def task_list(connexion : Connection) -> list :
    with connexion:
        # Returns list from index 1 cause index 0 is a special char, not a task
        return connexion.execute(TASK_LIST).fetchall()[1:]

def max_and_current_streaks(connexion : Connection, task : str) -> Tuple[str, str]:
    with connexion:
        return connexion.execute(MAX_AND_CURRENT_STREAK, [task]).fetchall()

def all_task_streaks(connexion : Connection):
    for task in task_list(connexion):
        streak = max_and_current_streaks(connexion, task[0])
        print(f"  Max streak for {task[0]} : {streak[0][0]}")

def past_weeks(connexion : Connection, number_of_weeks : int):
    with connexion :
        day_difference = 7
        for week_delta in list(range(1,number_of_weeks+1)):
            (monday,sunday) = connexion.execute(DATES, [f"-{day_difference * week_delta} days", f"-{day_difference * week_delta} days"]).fetchone()
            timer_per_task = connexion.execute(TOTAL_TIME_PARTICULAR_WEEK, [f"-{day_difference * week_delta} days", f"-{day_difference * week_delta} days"]).fetchall()
            print(f"Week from Monday {monday} to Sunday {sunday} : \n\t Total time : {timer_per_task[0][0]}")

if __name__ == '__main__':
    import sqlite3
    try:
        connexion = sqlite3.connect('timer_data.db')
        cursor = connexion.cursor()
        timers = connexion.execute('''SELECT * from timer_data WHERE date BETWEEN date('now', 'weekday 1', '-7 days') AND date('now', 'weekday 0', '-7 days')''').fetchall()

        print(len(timers))
        # Works
        # timer_per_task = connexion.execute(TOTAL_TIME_PARTICULAR_WEEK, [f"-7 days", f"-7 days"]).fetchall()
        # print(timer_per_task)
        past_weeks(connexion, 5)
        # print("done")
    except Exception as e :
        raise Exception(e)
