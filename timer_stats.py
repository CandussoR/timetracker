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

TOTAL_TIME_WEEK = '''
    SELECT printf("%02d:%02d:%02d", totsec / 3600, (totsec % 3600) / 60, (totsec % 86400) / 3600) as total
    FROM (
        SELECT sum(time_elapsed) as totsec
        FROM timer_data
        WHERE date(date) > date('now', 'weekday 0', '-7 days')
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

AVG_TIME_DAY = '''SELECT time(AVG(sum_time), 'unixepoch')
            FROM (
            SELECT sum(time_elapsed) as sum_time
            FROM timer_data
            WHERE date LIKE '2022%'
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

def timer_count(connexion, time_span):
    with connexion:
        if time_span == 'today':
            number = connexion.execute(TODAY_COUNT).fetchone()
        elif time_span == 'week':
            number = connexion.execute(WEEK_COUNT).fetchone()
        elif time_span == 'year':
            number = connexion.execute(YEAR_COUNT).fetchone()
    return number[0]

def total_time(connexion, time_span):
    with connexion:
        if time_span == 'today':
            timer_per_task = connexion.execute(TOTAL_TIME_TODAY).fetchone()
        elif time_span == 'week':
            timer_per_task = connexion.execute(TOTAL_TIME_WEEK).fetchone()
        elif time_span == 'year':
            timer_per_task = connexion.execute(TOTAL_TIME_YEAR).fetchone()
        return timer_per_task[0]

def time_per_task_today(connexion):
    with connexion:
        time_per_task = connexion.execute(TIME_PER_TASK_TODAY).fetchall()
    return time_per_task

def max_in_a_day(connexion):
    with connexion:
        max = connexion.execute(DAY_MAX).fetchone()
    return max

def average_day(connexion):
    with connexion:
        avg = connexion.execute(AVG_TIME_DAY).fetchone()
    return avg[0]

def task_list(connexion):
    with connexion:
        tasks = connexion.execute(TASK_LIST).fetchall()
        return tasks[1:]

def max_and_current_streaks(connexion, task):
    with connexion:
        task_streak = connexion.execute(MAX_AND_CURRENT_STREAK, [task]).fetchall()
    return task_streak

def all_task_streaks(connexion):
    all_tasks = task_list(connexion)
    for task in all_tasks:
        streak = max_and_current_streaks(connexion, task[0])
        print(f"Max streak for {task[0]} : {streak[0][0]}")
