from sqlite3 import connect
from typing import Optional, Tuple, Union
from sqlite3.dbapi2 import Connection
from datetime import datetime

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
            if time_span == 'today':
                total_count = "SELECT COUNT(*) FROM timer_data WHERE date(date) = date('now');"
                number = self.connexion.execute(total_count).fetchone()
            elif time_span == 'week':
                week_count = "SELECT COUNT(*) FROM timer_data WHERE date(date) > date('now', 'weekday 0', '-7 days')"
                number = self.connexion.execute(week_count).fetchone()
            elif time_span == 'year':
                year_count = "SELECT COUNT(*) FROM timer_data WHERE date(strftime('%Y', date)) = date(strftime('%Y', 'now'))"
                number = self.connexion.execute(year_count).fetchone()
        return number[0]

    def total_time(self, time_span : str) -> str :
        with self.connexion:
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
        for task in self.task_list(self.connexion):
            streak = self.max_and_current_streaks(task[0])
            print(f"  Max streak for {task[0]} : {streak[0][0]}")

    def past_weeks(self, number_of_weeks : int):
        with self.connexion :
            # Gets the dates of a certain number of weeks
            dates = self.calculate_past_weeks_dates(number_of_weeks)

            for date in dates:
                monday, sunday = date
                total_time_particular_week = '''
                    SELECT printf("%02d:%02d:%02d", totsec / 3600, (totsec % 3600) / 60, (totsec % 86400) / 3600) as total
                    FROM (
                        SELECT sum(time_elapsed) as totsec
                        FROM timer_data
                        WHERE date BETWEEN ? and ?
                        );'''
                timer_per_task = self.connexion.execute(total_time_particular_week, [monday, sunday]).fetchone()
                print(f"Week from Monday {monday} to Sunday {sunday} : \n\t Total time : {timer_per_task[0]}")

    def calculate_past_weeks_dates(self, number_of_weeks : int):
        # Getting the number of current day
        sqlite_weekday = int(self.connexion.execute('''SELECT strftime('%w', 'now');''').fetchone()[0])
        dates = "SELECT date('now', 'localtime', 'weekday 1', ?), date('now', 'localtime', 'weekday 0', ?)"
        dates = []
        day_difference = 7

        # The date function will seek the next date for the weekday specified if it isn't passed,
        # so we need to calculate for sunday, monday, and the others.
        if sqlite_weekday in range(2, 7):
            for week_delta in list(range(1,number_of_weeks+1)):
                dates.append(self.connexion.execute(dates, [f"-{day_difference * week_delta} days", f"-{day_difference * (week_delta - 1)} days"]).fetchone())
        elif sqlite_weekday == 1:
            for week_delta in list(range(1,number_of_weeks+1)):
                dates.append(self.connexion.execute(dates, [f"-{day_difference * week_delta} days", f"-{day_difference * week_delta} days"]).fetchone())
        elif sqlite_weekday == 0:
            for week_delta in list(range(1,number_of_weeks+1)):
                dates.append(self.connexion.execute(dates, [f"-{day_difference * (week_delta + 1)} days", f"-{day_difference * week_delta} days"]).fetchone())
        
        return dates