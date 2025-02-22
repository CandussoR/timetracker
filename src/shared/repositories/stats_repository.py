from sqlite3 import connect
from typing import Literal, Optional, Tuple, Union
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
        if connexion is None and db_name is None :
            raise ValueError("Either connexion or db_name must be passed.")
        if connexion : self.connexion = connexion
        elif db_name : self.connexion = connect(db_name)


    def get_first_and_last_date_in_db(self) -> tuple[str, str]:
        fd : str = self.connexion.execute('SELECT date FROM timer_data ORDER BY date ASC LIMIT 1;').fetchone()[0]
        ld : str = self.connexion.execute('SELECT date FROM timer_data ORDER BY date DESC LIMIT 1;').fetchone()[0]
        return fd, ld


    def timer_count(self, time_span : Optional[str] = None, params : Optional[dict] = None) -> int :
        assert time_span or params

        with self.connexion:
            from_clause = "FROM timer_data"
            where_clause = []

            if params:
                where_clause = self.build_where_clause_from_dict(params)
                from_clause = self.build_from_clause_from_dict(params)

            if time_span:
                if params:
                    assert set(params.keys()).intersection(["day", "weekStart", "month", "year", "rangeBeginning"]) == set(), "Shouldn't have multiple periods."
                if time_span == 'today':
                    where_clause.append("date(date) = date('now')")
                elif time_span == 'week':
                    where_clause.append("date(date) > date('now', 'weekday 0', '-7 days')")
                elif time_span == 'month':
                    where_clause.append("strftime('%Y-%m', date) = strftime('%Y-%m', 'now')")
                elif time_span == 'year':
                    where_clause.append("date(strftime('%Y', date)) = date(strftime('%Y', 'now'))")

            query = f'''SELECT COUNT(timer_data.id) {from_clause} WHERE {' AND '.join(where_clause)};'''                       
            return self.connexion.execute(query, params).fetchone()[0] if params else self.connexion.execute(query).fetchone()[0]


    def total_time(self, time_span : Optional[str] = None, params : Optional[dict] = None) -> float :
        assert time_span or params

        with self.connexion:
            from_clause = 'FROM timer_data'
            where_clause = []

            if params:
                where_clause = self.build_where_clause_from_dict(params)
                from_clause = self.build_from_clause_from_dict(params)
            if time_span:
                if params:
                    assert set(params.keys()).intersection(["day", "weekStart", "month", "year", "rangeBeginning"]) == set(), "Shouldn't have multiple periods."
                if time_span == 'today':
                    where_clause.append("date(date) = date('now');")
                elif time_span == 'week':
                    where_clause.append("date(date) > date('now', 'weekday 0', '-7 days');")
                elif time_span == 'month':
                    where_clause.append("strftime('%Y-%m', date) = strftime('%Y-%m', 'now');")
                elif time_span == 'year':
                    where_clause.append("date(strftime('%Y', date)) = date(strftime('%Y', 'now'));") 

        query = f"SELECT COALESCE(sum(time_elapsed), 0) as totsec {from_clause} WHERE {' AND '.join(where_clause)}"
        timer_count = self.connexion.execute(query, params).fetchone() if params else self.connexion.execute(query).fetchone()
        return timer_count[0]


    def total_time_per_day_in_range(self, params : dict) -> list[tuple] :
        '''
            Beginning and end are "YYYY-MM-DD" datestrings.
            Returns a list of (date, total) tuples.
        '''
        if not set(["task", "subtask", "tag"]).issubset(params):
            query = "SELECT date, SUM(time_elapsed) as total FROM timer_data WHERE date BETWEEN date(:rangeBeginning) AND date(:rangeEnding) GROUP BY date"
            return self.connexion.execute(query, params).fetchall()

        from_clause = self.build_from_clause_from_dict(params)
        where_clause = self.build_where_clause_from_dict(params)

        query = f"SELECT date, SUM(time_elapsed) {from_clause} WHERE {' AND '.join(where_clause)} GROUP BY date"
        return self.connexion.execute(query, params).fetchall()



    def total_time_per_week_in_range(self, beginning : str, end : str) -> list[tuple[str, float]]:
        '''
            Takes ints as week1 and week2, returns a tuple (num_week, time_per_week).
        '''
        query = '''WITH week_data AS (
            SELECT date, 
                SUM(CASE WHEN date < ? THEN 0 ELSE time_elapsed END) as time_elapsed_day, 
                date(date, 'weekday 1') AS week_start, 
                date(date, 'weekday 0', '+7 days') AS week_end 
                FROM timer_data 
                WHERE date >= date(?, 'weekday 1', '-7 days') 
                    AND date < date(?, 'weekday 0', '+7 days') 
                GROUP BY date 
            ) 
            SELECT SUM(time_elapsed_day) 
            FROM week_data
            WHERE date >= ? and date < ?
            GROUP BY week_end;'''
        return self.connexion.execute(query, (beginning, beginning, end, beginning, end)).fetchall()


    def total_time_per_month_in_range(self, month1 : str, month2 : str) -> list[tuple]:
        '''
            Takes strings as week1 and week2, returns a list of tuple (month, time_per_month).
        '''
        query= f'''
            WITH sub AS (
                SELECT 
                    strftime('%Y-%m', date) as month,
                    time_elapsed
                FROM timer_data
                    JOIN tasks ON timer_data.task_id = tasks.id
                WHERE date BETWEEN ? and ?
            ),
            sub2 AS (
                SELECT month,
                    SUM(time_elapsed) OVER (PARTITION BY month) as time_per_month,
                    ROW_NUMBER() OVER (PARTITION BY month) as row_num
                FROM sub
                ORDER BY month
            )
            SELECT month, time_per_month
            FROM sub2
            WHERE row_num = 1
            ORDER BY month ASC;
            '''
        return self.connexion.execute(query, (month1, month2)).fetchall()
    
    
    def total_time_per_year_in_range(self, years : list[str]) -> list[tuple]:
        query= f'''
            WITH sub AS (
                SELECT 
                    strftime('%Y', date) as year,
                    time_elapsed
                FROM timer_data
                WHERE date BETWEEN ? AND ?
            ),
            sub2 AS (
                SELECT year,
                    SUM(time_elapsed) OVER (PARTITION BY year) as time_per_year,
                    ROW_NUMBER() OVER (PARTITION BY year) as row_num
                FROM sub
                ORDER BY year
            )
            SELECT year, time_per_year
            FROM sub2
            WHERE row_num = 1
            ORDER BY year ASC;
            '''
        return self.connexion.execute(query, [*years]).fetchall() 

    def time_per_task_today(self) -> list[tuple]:
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

    def max_and_current_streaks(self, task : str) -> list[Tuple[str, str]]:
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


    def get_task_time_ratio(self, range : list[datetime], params : Optional[dict] = None) -> list[tuple]:
        '''
           Count time on task during a certain period of time,
           or time on subtasks of a certain task.
           Takes a dict with a period key for clarity and date(s) as strings, return a tuple (date, task, total_time, ratio)
        '''
        # Should refactor this too to get it more easily in the service.
        #TODO : Manage a full request with tag ?
        where_clause = self.build_where_clause_from_dict(params) if params else []
        date_where = "date = date(?)" if len(range) < 2 else "date BETWEEN date(?) AND date(?)"
        where_clause.insert(0, date_where)

        query = f"""
                WITH q as (
                    SELECT date,
                        t.task_name,
                        SUM(time_elapsed) as total_time
                    FROM timer_data
                    JOIN tasks t on t.id = timer_data.task_id
                    WHERE {' AND '.join(where_clause)}
                    GROUP BY task_name
                )
                SELECT task_name,
                    total_time,
                    ROUND((total_time/ (SELECT SUM(total_time) FROM q)*100), 1) as ratio
                    FROM q
                    GROUP BY task_name
                    ORDER BY ratio DESC;
                """
        return self.connexion.execute(query, [*range]).fetchall()


    def get_task_time_per_day_between(self, start : str, end : str):
        '''
            Param : start & end, strings.
            Returns (date, task_name, time_per_task, time_per_day, ratio).
        '''
        query = '''WITH tpd AS (
                        SELECT date, 
                            task_name, 
                            SUM(time_elapsed) OVER (PARTITION BY date, task_name) as time_per_task, 
                            SUM(time_elapsed) OVER (PARTITION BY date) as time_per_day, 
                            ROW_NUMBER() OVER (PARTITION BY date, task_name) as row_num 
                        FROM timer_data 
                        JOIN tasks ON tasks.id = timer_data.task_id 
                        WHERE date BETWEEN ? AND ?) 
                    SELECT date, 
                        task_name, 
                        time_per_day, 
                        time_per_task, 
                        ROUND((time_per_task/time_per_day)*100, 1) as ratio 
                    FROM tpd 
                    WHERE row_num = 1 
                    ORDER BY date;'''
        return self.connexion.execute(query, [start,end]).fetchall()


    def total_time_per_week_for_year(self, year : Optional[str] = None, include_partial : bool = True) -> list[tuple[str, str, float]]:
        '''
           Used for the BarChart in the year stats in the front.
           Potentially takes a list of years and returns an array of (year, week, week_start, week_end, total_time).
        '''
        # If no year, get the first and the last timer to use as beginning and end.
        if not year:
            year = self.connexion.execute("SELECT strftime('%Y', date('now'))").fetchone()[0]
        calendar_beginning = f'{year}-01-01'
        calendar_ending = f'{year}-12-31'
        first_week_zero = self.connexion.execute("SELECT strftime('%W', ?);", (calendar_beginning,)).fetchone()[0] == '00'

        query = f"""WITH RECURSIVE dates(year, day, date) AS ( 
                    SELECT strftime('%Y', '{calendar_beginning}'), 
                        strftime('%w', '{calendar_beginning}'), 
                        '{calendar_beginning}' 
                    UNION ALL 
                    SELECT strftime('%Y', date(date, '+1 day')), 
                        strftime('%w', date(date, '+1 day')), 
                        DATE(date, '+1 day') 
                    FROM dates 
                    WHERE date < '{calendar_ending}' ), 
                    weeks AS (
                        SELECT *, 
                            SUM(CASE WHEN day = '1' THEN 1 ELSE 0 END) OVER (ORDER BY dates.date) {'+ 1' if first_week_zero else ''} as week 
                        FROM dates
                    ),
                    calendar AS (
                        SELECT year,
                            date,
                            week,
                            day
                        FROM weeks
                    ),
                    { '''week_day_count AS (
                        SELECT year,
                            date,
                            week,
                            COUNT(*) OVER (PARTITION BY year, week) as cnt_days
                        FROM calendar
                        ORDER BY year
                    ),
                    full_weeks AS (
                        SELECT year,
                            week,
                            date
                        FROM week_day_count
                        WHERE cnt_days = 7
                    ),''' if not include_partial else '' }
                    total_time_week AS (
                        SELECT sq.year,
                            sq.week,
                            t.time_elapsed,
                            SUM(COALESCE(t.time_elapsed,0)) OVER (PARTITION BY sq.year, sq.week) as total_time_worked
                        FROM {'calendar' if include_partial else 'full_weeks'} sq
                            LEFT JOIN timer_data t ON sq.date = t.date
                    )
                    SELECT year,
                        week,
                        total_time_worked
                    FROM total_time_week
                    GROUP BY week;
                """
        return self.connexion.execute(query).fetchall()
    
    
    def get_task_time_ratio_by_week_between(self, begin : str, end : str, include_partial : bool = True):
        '''
            Returns a list of tuples (num_week_group, task_name, total time of task, total time of week, ratio).  
        '''
        query = f'''WITH RECURSIVE dates(d, weekday) AS ( 
            SELECT ?, strftime('%w', ?) 
            UNION ALL 
            SELECT DATE(d, '+1 day'), strftime('%w', date(d, '+1 day'))
            FROM dates 
            WHERE d < DATE(?, '-1 day')
            ), 
            weeks AS (
            SELECT *, 
                SUM(CASE WHEN weekday = '1' THEN 1 ELSE 0 END) OVER (ORDER BY dates.d) as week_group 
                FROM dates
            ),
            counted_weeks AS (
                SELECT *, COUNT(*) OVER (PARTITION BY week_group) as days_in_week 
                FROM weeks
            ),
            total_time_week AS (
                SELECT week_group, 
                    SUM(COALESCE(time_elapsed, 0)) AS total_time_week 
                FROM weeks 
                JOIN timer_data ON weeks.d = timer_data.date 
                { 'WHERE cw.days_in_week = 7' if not include_partial else '' }
                GROUP BY week_group
            ), time_task_week AS (
                SELECT cw.d, week_group, task_name, COALESCE(time_elapsed, 0) AS time_elapsed, SUM(COALESCE(time_elapsed, 0)) OVER (PARTITION BY week_group, task_name) as total_time_task_week
                FROM counted_weeks cw 
                LEFT JOIN timer_data td ON td.date = cw.d 
                LEFT JOIN tasks ON td.task_id = tasks.id 
                WHERE task_name IS NOT NULL
            ) 
            SELECT ttt.week_group, ttt.task_name, ttt.total_time_task_week, total_time_week, ROUND((total_time_task_week/total_time_week)*100, 1) as ratio 
            FROM time_task_week ttt
            JOIN total_time_week ON total_time_week.week_group = ttt.week_group 
            GROUP BY ttt.week_group, task_name
            ORDER BY ttt.week_group;
        '''
        return self.connexion.execute(query, [begin, begin, end]).fetchall()
        
        
    def get_total_week_time_between(self, begin : str, end : str, include_partial : bool = True):
        '''
            Returns a list of tuple (week_group, total_time).
        '''
        query = f'''WITH RECURSIVE dates(d, weekday) AS ( 
            SELECT ?, strftime('%w', ?) 
            UNION ALL 
            SELECT DATE(d, '+1 day'), strftime('%w', date(d, '+1 day'))
            FROM dates 
            WHERE d < DATE(?, '-1 day')
            ), 
            weeks AS (
            SELECT *, 
                SUM(CASE WHEN weekday = '1' THEN 1 ELSE 0 END) OVER (ORDER BY dates.d) as week_group 
                FROM dates
            ),
            counted_weeks AS (
                SELECT *, COUNT(*) OVER (PARTITION BY week_group) as days_in_week 
                FROM weeks
            )
            SELECT week_group,
                SUM(COALESCE(time_elapsed, 0)) AS total_time_week 
            FROM counted_weeks cw
            LEFT JOIN timer_data ON cw.d = timer_data.date 
            { 'WHERE cw.days_in_week = 7' if not include_partial else '' }
            GROUP BY week_group;'''
        return self.connexion.execute(query, [begin, begin, end]).fetchall()


    def get_task_time_per_month_in_year(self, year : str):
        '''
            Gets a year string date 'YYYY'.
            Returns (num_month, task_name, time_per_task, time_per_month, ratio).
        '''
        beginning = f"{year}-01-01"
        end = f"{int(year)+1}-01-01"
        query= f'''
                WITH sub AS (
                    SELECT date,
                        task_name,
                        strftime('%Y-%m', date) as num_month,
                        time_elapsed
                    FROM timer_data
                        JOIN tasks ON timer_data.task_id = tasks.id
                    WHERE date >= ? and date < ?
                ),
                sub2 AS (
                    SELECT date,
                        num_month,
                        task_name,
                        SUM(time_elapsed) OVER (PARTITION BY task_name, num_month) AS time_per_task,
                        SUM(time_elapsed) OVER (PARTITION BY num_month) as time_per_month,
                        ROW_NUMBER() OVER (PARTITION BY num_month, task_name) as row_num
                    FROM sub
                    ORDER BY num_month
                ),
                sub3 AS (
                    SELECT date,
                        num_month,
                        task_name,
                        time_per_task,
                        time_per_month
                    FROM sub2
                    WHERE row_num = 1
                )
                SELECT num_month, 
                    task_name, 
                    time_per_task, 
                    time_per_month,
                    ROUND((time_per_task/time_per_month)*100, 1) as ratio
                FROM sub3
                ORDER BY num_month;
                '''
        return self.connexion.execute(query, (beginning,end)).fetchall()
    

    def get_subtask_time_ratio(self, params : dict) -> list[tuple]:
        keys = params.keys()
        if not "task" in keys: raise KeyError("Cannot get subtask ratio without a task.")
        where_clause = self.build_where_clause_from_dict(params)
        tag = "tag" in keys
        query = f'''WITH base AS (
                         SELECT tasks.task_name, 
                             tasks.subtask, 
                             time_elapsed, 
                             SUM(time_elapsed) OVER (PARTITION BY tasks.task_name) AS time_for_task, 
                             SUM(time_elapsed) OVER (PARTITION BY tasks.task_name, tasks.subtask) AS time_for_subtask 
                         FROM timer_data 
                         JOIN tasks ON tasks.id = timer_data.task_id 
                         {"JOIN tags ON tags.id = timer_data.tag_id" if tag else ""}
                         WHERE {' AND '.join(where_clause)}), 
                     numbered AS (
                         SELECT *, ROW_NUMBER() OVER (PARTITION BY task_name, subtask) as row_num 
                         FROM base) 
                     SELECT task_name, 
                         subtask, 
                         time_for_subtask, 
                         ROUND((time_for_subtask/time_for_task)* 100, 1) AS ratio 
                     FROM numbered 
                     WHERE row_num = 1
                     ORDER BY ratio DESC, subtask ASC;'''
        return self.connexion.execute(query, params).fetchall()
    

    def mean_time_per_period(self, period : Literal["day", "week", "month", "year"]) -> int:
        '''Returns an int which is the time elapsed in seconds.'''
        match period:
            case "day":
                query = '''WITH f AS (
                            SELECT SUM(time_elapsed) OVER (PARTITION BY date) as total_day, ROW_NUMBER() OVER (PARTITION BY date) as row_num 
                            FROM timer_data 
                            WHERE strftime('%Y', date) = strftime('%Y', 'now')) 
                           SELECT COALESCE(AVG(total_day),0) as mean_day FROM f WHERE row_num= 1;'''
                return self.connexion.execute(query).fetchone()[0]
            case "week":
                query = '''WITH f AS (
                            SELECT SUM(time_elapsed) OVER (PARTITION BY strftime('%W', date)) as total_week, ROW_NUMBER() OVER (PARTITION BY strftime('%W', date)) as row_num 
                            FROM timer_data 
                            WHERE strftime('%Y', date) = strftime('%Y', 'now')) 
                            SELECT COALESCE(AVG(total_week),0) as mean_week FROM f WHERE row_num = 1;'''
                return self.connexion.execute(query).fetchone()[0]
            case "month":
                query = '''WITH f AS (
                            SELECT SUM(time_elapsed) OVER (PARTITION BY strftime('%Y-%m', date)) as total_week, ROW_NUMBER() OVER (PARTITION BY strftime('%Y-%m', date)) as row_num 
                            FROM timer_data 
                            WHERE strftime('%Y', date) = strftime('%Y', 'now')) 
                            SELECT COALESCE(AVG(total_week),0) as mean_week FROM f WHERE row_num = 1;'''
                return self.connexion.execute(query).fetchone()[0]
            case "year":
                raise NotImplementedError('Not implemented yet.')
    
    def build_where_clause_from_dict(self, params : dict):
        '''
            Takes a dict a build the where clause of a SQlite query.
            Dict might expect the following keys :
            day, week, month, year, weekStart, weekEnd, rangeBeginning, rangeEnding, task, subtask, logSearch.
        '''
        parameters = []
        keys = params.keys()
        if "day" in keys:
            parameters.append("date = (:day)")
        elif set(["weekStart", "weekEnd"]).issubset(keys):
            parameters.append(f"date BETWEEN (:weekStart) AND (:weekEnd)")
        elif "month" in keys:
            parameters.append(f"strftime('%Y-%m', date) = (:month)")
        elif "year" in keys :
            parameters.append(f"strftime('%Y', date) = (:year)")
        elif set(["rangeBeginning", "rangeEnding"]).issubset(keys):
            parameters.append("date BETWEEN (:rangeBeginning) AND (:rangeEnding)")

        if "task" in keys and not "subtask" in keys:
            parameters.append("tasks.task_name = (:task)")
        elif set(["task", "subtask"]).issubset(keys):
            parameters.append("tasks.task_name = (:task) AND tasks.subtask = (:subtask)")

        if "tag" in keys:
            parameters.append("tags.tag = (:tag)")

        if "logSearch" in keys:
            parameters.append("log LIKE '%(:logSearch)%'")
        return parameters
    

    def build_from_clause_from_dict(self, d : dict) -> str:
        from_clause = []
        for k in d.keys():
            if k == 'task' :
               from_clause.append("JOIN tasks ON tasks.id = timer_data.task_id")
            if k == 'tag' :
                from_clause.append("JOIN tags ON tags.id = timer_data.tag_id")
        return f"FROM timer_data {' '.join(from_clause)}"


    def get_task_time(self, per_period : str, dates : list[datetime]) -> list[tuple[str,str,float,float,float]]:
        '''
            Used to return the data destined to the apex stacked column chart.
            Takes a period (day, week, month or year) and a list of two dates.
            Returns a list of (date, task_name, time_per_task, time_per_period, ratio).
        '''
        if per_period not in ["day", "week", "month", "year"] : raise ValueError(f"Wrong period ({per_period}).")
        if len(dates) != 2 : raise ValueError("There must be two dates.")

        range_dict = {"rangeBeginning" : dates[0], "rangeEnding" : dates[1]}
        strftime = {
            "week" : "strftime('%Y-%W', date)" if dates[0].year != dates[1].year else "strftime('%W', date)",
            "month": "strftime('%Y-%m', date)",
            "year": "strftime('%Y', date)"
        }

        query = f'''WITH sub AS (
                    SELECT task_name,
                        {"date" if per_period == 'day' else strftime[per_period]} as time_period,
                        time_elapsed
                    FROM timer_data
                        JOIN tasks ON timer_data.task_id = tasks.id
                    WHERE strftime('%Y-%m-%d', date) BETWEEN date(:rangeBeginning) AND date(:rangeEnding)
                    ),
                    last_sub AS (
                    SELECT time_period,
                        task_name,
                        SUM(time_elapsed) OVER (PARTITION BY task_name, time_period) AS time_per_task,
                        SUM(time_elapsed) OVER (PARTITION BY time_period) as time_per_period,
                        ROW_NUMBER() OVER (PARTITION BY time_period, task_name) as row_num
                    FROM sub
                    ORDER BY time_period
                )
                SELECT time_period, 
                        task_name, 
                        time_per_period, 
                        time_per_task, 
                        ROUND((time_per_task/time_per_period)*100, 1) as ratio 
                FROM last_sub 
                WHERE row_num = 1 
                ORDER BY time_period;
                '''
        return self.connexion.execute(query, range_dict).fetchall()
