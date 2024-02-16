from sqlite3 import connect
from typing import Optional, Tuple, Union
from sqlite3.dbapi2 import Connection
from datetime import datetime, timedelta

class SqliteStatRepository():

    SELECT_WEEK_TIMERS = '''
            SELECT *
            FROM timer_data
            WHERE date(date) BETWEEN date('now', 'weekday 1', ?) and date('now', 'weekday 0', ?);'''

    AVG_TIME_DAY = '''SELECT time(AVG(sum_time), 'unixepoch')
                FROM (
                SELECT sum(time_elapsed) as sum_time
                FROM timer_data
                WHERE date LIKE (?)
                GROUP BY date
                );'''

    def __init__(self, connexion : Optional[Connection] = None, db_name : Optional[str] = None) :
        self.connexion = connexion if connexion is not None else connect(db_name)

    def timer_count(self, time_span : str) -> int :
        with self.connexion:
            try:

                if time_span == 'today':
                    total_count = "SELECT COUNT(*) FROM timer_data WHERE date(date) = date('now');"
                    number = self.connexion.execute(total_count).fetchone()
                elif time_span == 'week':
                    week_count = "SELECT COUNT(*) FROM timer_data WHERE date(date) > date('now', 'weekday 0', '-7 days')"
                    number = self.connexion.execute(week_count).fetchone()
                elif time_span == 'month':
                    month_count = "SELECT COUNT(*) FROM timer_data WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')"
                    print("month count")
                    number = self.connexion.execute(month_count).fetchone()
                elif time_span == 'year':
                    year_count = "SELECT COUNT(*) FROM timer_data WHERE date(strftime('%Y', date)) = date(strftime('%Y', 'now'))"
                    number = self.connexion.execute(year_count).fetchone()

                return number[0]

            except Exception as e:
                print("exception in timer count")
                raise Exception(e) from e

    def total_time(self, time_span : str) -> str :
        with self.connexion:
            try:
                if time_span == 'today':
                    total_time_today = '''SELECT time(sum(time_elapsed), 'unixepoch') FROM timer_data
                            WHERE date(date) = date('now');'''
                    timer_per_task = self.connexion.execute(total_time_today).fetchone()
                elif time_span == 'week':
                    total_time_this_week = '''
                        SELECT printf("%02d:%02d:%02d", totsec / 3600, (totsec % 3600) / 60, totsec % 60) as total
                        FROM (
                            SELECT sum(time_elapsed) as totsec
                            FROM timer_data
                            WHERE date(date) > date('now', 'weekday 0', '-7 days')
                            );'''
                    timer_per_task = self.connexion.execute(total_time_this_week).fetchone()
                elif time_span == 'month':
                    total_time_month = '''
                        SELECT printf("%02d:%02d:%02d:%02d",
                                    totsec / 86400,
                                    (totsec % 86400) / 3600,
                                    (totsec % 3600) / 60,
                                    totsec % 60) as total
                        FROM (
                            SELECT sum(time_elapsed) as totsec
                            FROM timer_data
                            WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
                            );'''
                    timer_per_task = self.connexion.execute(total_time_month).fetchone()
                elif time_span == 'year':
                    total_time_year = '''
                        SELECT printf("%02d:%02d:%02d:%02d",
                                    totsec / 86400,
                                    (totsec % 86400) / 3600,
                                    (totsec % 3600) / 60,
                                    totsec % 60) as total
                        FROM (
                            SELECT sum(time_elapsed) as totsec
                            FROM timer_data
                            WHERE date(strftime('%Y', date)) = date(strftime('%Y', 'now'))
                            );'''
                    timer_per_task = self.connexion.execute(total_time_year).fetchone()
                return timer_per_task[0]
            except Exception as e:
                raise Exception(e) from e

    def total_time_per_day_in_range(self, beginning : str, end : str) -> list[tuple]:
        '''
            Beginning and end are "YYYY-MM-DD" datestrings.
            Returns a list of (date, total) tuples.
        '''
        query = "SELECT date, SUM(time_elapsed) as total FROM timer_data WHERE date BETWEEN ? AND ? GROUP BY date"
        return self.connexion.execute(query, [beginning, end]).fetchall()

    def time_per_task_today(self) -> str:
        with self.connexion:
            time_per_task_today = '''SELECT t.task_name, time(sum(time_elapsed), 'unixepoch') as time
                            FROM timer_data td
                            JOIN tasks t ON t.id = td.task_id
                            WHERE date(date) = date('now')
                            GROUP BY t.task_name
                            ORDER BY time DESC;'''
            return self.connexion.execute(time_per_task_today).fetchall()

    def max_in_a_day(self) -> Tuple[str, str]:
        with self.connexion:
            day_max = '''SELECT date, MAX(sum_time)
                        FROM (
                        SELECT date, time(sum(time_elapsed), 'unixepoch') as sum_time
                        FROM timer_data
                        GROUP BY date);'''
            return self.connexion.execute(day_max).fetchone()

    def all_time_average_day(self) -> str:
        with self.connexion:
            avg_time_all_days = '''SELECT time(AVG(sum_time), 'unixepoch')
                        FROM (
                        SELECT sum(time_elapsed) as sum_time
                        FROM timer_data
                        );'''
            return self.connexion.execute(avg_time_all_days).fetchone()[0]

    def average_day_this_year(self) -> str:
        with self.connexion:
            return self.connexion.execute(self.AVG_TIME_DAY, [f"{datetime.now().year}%"]).fetchone()[0]

    def average_day_for_year(self, year : Union[str, int]) -> str:
        with self.connexion:
            return self.connexion.execute(self.AVG_TIME_DAY, [f"{str(year)}%"]).fetchone()[0]

    def task_list(self) -> list :
        with self.connexion:
            # Returns list from index 1 cause index 0 is a special char, not a task
            return self.connexion.execute( 'SELECT DISTINCT task_name FROM tasks;').fetchall()[1:]

    def max_and_current_streaks(self, task : str) -> Tuple[str, str]:
        with self.connexion:
            max_and_current_streak ='''
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
            return self.connexion.execute(max_and_current_streak, [task]).fetchall()

    def all_task_streaks(self):
        task_streaks = []
        for task in self.task_list():
            streak = self.max_and_current_streaks(task[0])
            if streak:
                task_streaks.append((task[0], streak[0][0], streak[0][1]))
        return sorted(task_streaks, key = lambda x: x[1], reverse = True)

    def past_weeks(self, number_of_weeks : int):
        with self.connexion :
            # Gets the dates of a certain number of weeks
            dates = self.calculate_past_weeks_dates(number_of_weeks)

            weeks = []
            for date in dates:
                monday, sunday = date
                total_time_particular_week = '''
                    SELECT printf("%02d:%02d:%02d", totsec / 3600, (totsec % 3600) / 60, (totsec % 86400) / 3600) as total
                    FROM (
                        SELECT sum(time_elapsed) as totsec
                        FROM timer_data
                        WHERE date BETWEEN ? and ?
                        );'''
                time_per_week = self.connexion.execute(total_time_particular_week, [monday, sunday]).fetchone()[0]
                weeks.append((monday, sunday, time_per_week))
            return weeks

    def calculate_past_weeks_dates(self, number_of_weeks : int):
        # Getting the number of current day
        sqlite_weekday = int(self.connexion.execute('''SELECT strftime('%w', 'now');''').fetchone()[0])
        query = "SELECT date('now', 'localtime', 'weekday 1', ?), date('now', 'localtime', 'weekday 0', ?)"
        dates = []
        day_difference = 7

        # The date function will seek the next date for the weekday specified if it isn't passed,
        # so we need to calculate for sunday, monday, and the others.
        if sqlite_weekday in range(2, 7):
            for week_delta in list(range(1,number_of_weeks+1)):
                dates.append(self.connexion.execute(query, [f"-{day_difference * week_delta} days", f"-{day_difference * (week_delta - 1)} days"]).fetchone())
        elif sqlite_weekday == 1:
            for week_delta in list(range(1,number_of_weeks+1)):
                dates.append(self.connexion.execute(query, [f"-{day_difference * week_delta} days", f"-{day_difference * week_delta} days"]).fetchone())
        elif sqlite_weekday == 0:
            for week_delta in list(range(1,number_of_weeks+1)):
                dates.append(self.connexion.execute(query, [f"-{day_difference * (week_delta + 1)} days", f"-{day_difference * week_delta} days"]).fetchone())

        return dates

    def total_time_per_week(self, years : list[int|str] = None) -> list[tuple]:
        '''Potentially takes a list of years and returns an array of (year, week, week_start, week_end, total_time).'''

        # If no year, get the first and the last timer to use as beginning and end.
        if not years:
            calendar_begining, calendar_ending = self.connexion.execute("SELECT MIN(date), MAX(date) FROM timer_data").fetchone()
        else:
            calendar_begining = f'{years[0]}-01-01'
            calendar_ending = f'{years[-1]}-12-31'

        query = f"""
                    WITH RECURSIVE dates(year, week, day, date) AS (
                        VALUES(
                                strftime('%Y', '{calendar_begining}'),
                                strftime('%W', '{calendar_begining}'),
                                strftime('%w', '{calendar_begining}'),
                                '{calendar_begining}'
                            )
                        UNION ALL
                        SELECT strftime('%Y', DATE(date, '+1 day')),
                            strftime('%W', DATE(date, '+1 day')),
                            strftime('%w', DATE(date, '+1 day')),
                            DATE(date, '+1 day')
                        FROM dates
                        WHERE date < '{calendar_ending}'
                    ),
                    calendar AS (
                        SELECT year,
                            date,
                            week,
                            day,
                            DATE(date, '-' || (CAST(day AS INTEGER) + 1) || ' day', 'weekday 1') as start_of_week,
                            DATE( date, '+' || (6 - CAST(day AS INTEGER)) || ' day', 'weekday 0') as end_of_week
                        FROM dates
                    ),
                    week_day_count AS (
                        SELECT year,
                            date,
                            week,
                            start_of_week,
                            end_of_week,
                            COUNT(*) OVER (PARTITION BY year, week) as cnt_days
                        FROM calendar
                        ORDER BY year
                    ),
                    full_weeks AS (
                        SELECT year,
                            week,
                            start_of_week,
                            end_of_week,
                            date
                        FROM week_day_count
                        WHERE cnt_days = 7
                    ),
                    total_time_week AS (
                        SELECT fw.year,
                            fw.week,
                            fw.start_of_week,
                            fw.end_of_week,
                            fw.date,
                            t.time_elapsed,
                            SUM(COALESCE(t.time_elapsed,0)) OVER (PARTITION BY fw.year, fw.week) as total_time_worked
                        FROM full_weeks fw
                            LEFT JOIN timer_data t ON fw.date = t.date
                    )
                    SELECT year,
                        week,
                        start_of_week,
                        end_of_week,
                        total_time_worked
                    FROM total_time_week
                    GROUP BY week;
                """
        return self.connexion.execute(query).fetchall()

    def get_task_time_ratio(self, params) -> list[tuple]:
        '''
            Count time on task during a certain period of time,
           or time on subtasks of a certain task.
           Takes a dict with a period key, return a tuple (date, task, total_time, ratio)'''
        where_clause = ''
        # if params.get("date") is not None:
        #     if isinstance(params["date"], str):
        #         where_clause = f"WHERE date = \'{params['date']}\'"

        #     if isinstance(params["date"], list):
        #         [begin, end] = params["date"]
        #         where_clause = f"WHERE date BETWEEN {begin} AND {end}"
        date = "date('now')" if params.get("date") is None else f"\'{params['date']}\'"
        if params["period"] == "day":
            where_clause = f"WHERE date = {date}"
        elif params["period"] == "week":
            where_clause = "WHERE date > date('now', 'weekday 0', '-7 days')"
        elif params["period"] == "month":
            where_clause = "WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')"
        else :
            where_clause = "WHERE strftime('%Y', date) = strftime('%Y', 'now')"

        query = f"""
                WITH q as (
                    SELECT date,
                        t.task_name,
                        SUM(time_elapsed) as total_time
                    FROM timer_data
                    JOIN tasks t on t.id = timer_data.task_id
                    {where_clause}
                    GROUP BY task_name
                )
                SELECT date,
                    task_name,
                    total_time,
                    ROUND((total_time/ (SELECT SUM(total_time) FROM q)*100), 1) as ratio
                    FROM q
                    GROUP BY task_name
                    ORDER BY ratio DESC;
                """
        return self.connexion.execute(query).fetchall()
    
    def get_task_time_per_week_in_month(self, month : str):
        '''
            Returns (num_week, task_name, time_per_task, time_per_week, ratio).
        '''
        month = f"\'{month}\'"
        query= f'''
                WITH sub AS (
                    SELECT date,
                        task_name,
                        strftime('%W', date) as num_week,
                        time_elapsed
                    FROM timer_data
                        JOIN tasks ON timer_data.task_id = tasks.id
                    WHERE strftime('%Y-%m', date) LIKE {month}
                ),
                sub2 AS (
                    SELECT date,
                        num_week,
                        task_name,
                        SUM(time_elapsed) OVER (PARTITION BY task_name, num_week) AS time_per_task,
                        SUM(time_elapsed) OVER (PARTITION BY num_week) as time_per_week,
                        ROW_NUMBER() OVER (PARTITION BY num_week, task_name) as row_num
                    FROM sub
                    ORDER BY num_week
                ),
                sub3 AS (
                    SELECT date,
                        num_week,
                        task_name,
                        time_per_task,
                        time_per_week
                    FROM sub2
                    WHERE row_num = 1
                )
                SELECT num_week, 
                    task_name, 
                    time_per_task, 
                    time_per_week,
                    ROUND((time_per_task/time_per_week)*100, 1) as ratio
                FROM sub3;
                '''
        return self.connexion.execute(query).fetchall()

