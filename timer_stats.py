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
    SELECT printf("%02d:%02d:%02d:%02d", totsec / 86400, (totsec % 86400) / 3600, (totsec % 3600) / 60, (totsec % 86400) / 3600) as total
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
