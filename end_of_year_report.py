# .headers on
# .mode column/list
# .separator "|" / .separator ","

from typing import Literal
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

YEAR_IN_TASK = """
            with task_total_time AS (
                SELECT task_name,
                    date,
                    SUM(time_elapsed) OVER (PARTITION BY task_name) as time_elapsed,
                    ROW_NUMBER() OVER (PARTITION BY task_name) as row_num
                FROM timer_data td
                    JOIN tasks ON td.task_id = tasks.id
                WHERE date LIKE '2023%'
            ),
            dates_tasks AS (
                SELECT date,
                    task_name,
                    ROW_NUMBER() OVER (
                        PARTITION BY date,
                        task_name
                        ORDER BY date
                    ) as row_num_2
                FROM task_total_time
            ),
            task_day_count AS (
                SELECT task_name,
                    COUNT(task_name) AS cnt
                FROM dates_tasks
                GROUP BY task_name
            )
            SELECT tdc.task_name,
                tdc.cnt,
                ttt.time_elapsed
            FROM task_day_count tdc
                JOIN task_total_time ttt ON tdc.task_name = ttt.task_name
            GROUP BY tdc.task_name
            ORDER BY ttt.time_elapsed DESC;
            """

# Create a calendar and joins timer_data : shows not-worked day as well as worked.
MEAN_TIME_WORKED_AND_UNWORKED = """WITH RECURSIVE dates(day,date) AS ( 
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
    """

def total_time_per_week(years : list[int|str] = None) -> list[tuple]:
    # If no year, get the first and the last timer to use as beginning and end.
    if not years:
        calendar_begining, calendar_ending = connexion.execute("SELECT MIN(date), MAX(date) FROM timer_data").fetchone()
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
    return connexion.execute(query).fetchall()


def total_time_for_year(years : list[int|str] = None) -> list[tuple]:
    '''
       If no year list passed, queries the entire database.
       Returns a list of tuples (year, total time, percentage compared to previous year).
    '''
    params = []
    if years : 
        years = [str(y) for y in years]
        params = [*years]
    where_clause = "WHERE strftime('%Y', date) IN ({})".format(",".join(["?" for _ in years])) if years else ""
    query = f"""
                        WITH total_year_time AS (
                            SELECT strftime('%Y', date) as year,
                                SUM(time_elapsed) OVER (PARTITION BY strftime('%Y', date)) as total_time_year
                            FROM timer_data
                            {where_clause}
                        ),
                        grps AS (
                            SELECT *
                            FROM total_year_time
                            GROUP BY year
                        )
                        SELECT year,
                            total_time_year,
                            ROUND(
                                100 * (
                                    1 * total_time_year / LAG(total_time_year) OVER (
                                        ORDER BY year ASC
                                    ) - 1
                                ),
                                1
                            ) as time_previous_year
                        FROM grps;                   
                        """
    return connexion.execute(query, params).fetchall()


def format_time(time: float | int, max_unit: Literal["day", "hour"] = "hour") -> str:
    if max_unit == "day":
        return "{:02d}:{:02d}:{:02d}:{:02d}".format(
            int((time // 86400)),
            int((time % 86400) // 3600),
            int((time % 3600) // 60),
            int(time % 60),
        )
    else:
        return "{:02d}:{:02d}:{:02d}".format(
            int(time // 3600), int((time % 3600) // 60), int(time % 60)
        )


def total_time_for_each_task_for_years(years: list[int | str] = None, tasks: list[str] = None) -> list[tuple]:
    """Returns a list of tuples (year, task, total_time, percent)."""
    if years:
        years = [str(y) for y in years]

    years_query = "strftime('%Y', date) IN ( ({})".format(",".join(["?" for _ in years])) if years else ""
    task_query = "task_name IN ({})".format(",".join(["?" for _ in tasks])) if tasks else ""

    if years and tasks:
        where_clause = f"""WHERE {years_query} AND {task_query}"""
        params = [*years, *tasks]
    elif years:
        where_clause = f"""WHERE {years_query}"""
        params = [*years]
    elif tasks:
        where_clause = f"""WHERE {task_query}"""
        params = [*tasks]
    else:
        where_clause = ""
        params = []

    query = f"""
            with task_per_year AS (
                SELECT strftime('%Y', date) as year,
                    task_name,
                    SUM(time_elapsed) OVER (PARTITION BY strftime('%Y', date), task_name) as total_time_year
                FROM timer_data td
                    JOIN tasks t ON td.task_id = t.id
                {where_clause}
            )
            SELECT year,
                task_name,
                total_time_year,
                ROUND(
                    100 * (
                        total_time_year / LAG(total_time_year, 1, 0) OVER (PARTITION BY task_name) - 1
                    ),
                    1
                ) as previous_total_time
            FROM task_per_year
            GROUP BY year,
                task_name
            ORDER BY task_name;
            """
    return connexion.execute(query, params).fetchall()


def count_task_for_each_days(years: list[int | str] = None) -> list[tuple]:
    params = []
    if years : 
        where_clause = "WHERE strftime('%Y', date) IN ({})".format(",".join(["?" for _ in years])) if years else ""
        params = [str(year) for year in years]
    query = f"""
                with task_per_year AS (
                    SELECT strftime('%Y', date) as year,
                        task_name,
                        strftime('%w', date) as day,
                        COUNT(*) OVER (PARTITION BY strftime('%Y', date), strftime('%w', date), task_name) as total_per_day
                    FROM timer_data td
                        JOIN tasks t ON td.task_id = t.id
                    {where_clause}
                )
                SELECT year,
                    task_name,
                    MAX( CASE WHEN day = '1' THEN total_per_day END) as monday,
                    MAX( CASE WHEN day = '2' THEN total_per_day END) as tuesday,
                    MAX( CASE WHEN day = '3' THEN total_per_day END) as wednesday,
                    MAX( CASE WHEN day = '4' THEN total_per_day END) as thursday,
                    MAX( CASE WHEN day = '5' THEN total_per_day END) as friday,
                    MAX( CASE WHEN day = '6' THEN total_per_day END) as saturday,
                    MAX( CASE WHEN day = '0' THEN total_per_day END) as sunday
                FROM task_per_year
                GROUP BY year, task_name
                ORDER BY task_name;
    """
    return connexion.execute(query, params).fetchall()


def count_days_with_task_in_month_for_years(years: list[int | str] = None,) -> list[tuple]:
    '''
        If not year list is passed, queries the entire database.  
        Returns a list of tuple of length 13 or 14 with year (if any), task name, and each month.
    '''
    params = []
    if years : 
        where_clause = "WHERE strftime('%Y', date) IN ({})".format(",".join(["?" for _ in years])) if years else ""
        params = [str(year) for year in years]
    query = f"""
                with task_per_month AS (
                    SELECT {"strftime('%Y', date) as year"},
                        strftime('%m', date) as month,
                        task_name
                    FROM timer_data td
                        JOIN tasks t ON td.task_id = t.id
                    {where_clause}
                    GROUP BY year,
                        month,
                        date,
                        task_name
                    ORDER BY date
                ),
                counts AS (
                    SELECT *,
                        COUNT(*) OVER (PARTITION BY year, month, task_name) as cnt
                    FROM task_per_month
                )
                SELECT year,
                    task_name,
                    MAX( CASE WHEN month = '01' THEN cnt ELSE 0 END) as jan,
                    MAX( CASE WHEN month = '02' THEN cnt  ELSE 0 END) as feb,
                    MAX( CASE WHEN month = '03' THEN cnt ELSE 0 END) as mar,
                    MAX( CASE WHEN month = '04' THEN cnt ELSE 0 END) as apr,
                    MAX( CASE WHEN month = '05' THEN cnt ELSE 0 END) as may,
                    MAX( CASE WHEN month = '06' THEN cnt ELSE 0 END) as june,
                    MAX( CASE WHEN month = '07' THEN cnt ELSE 0 END) as july,
                    MAX( CASE WHEN month = '08' THEN cnt ELSE 0 END) as aug,
                    MAX( CASE WHEN month = '09' THEN cnt ELSE 0 END) as sept,
                    MAX( CASE WHEN month = '10' THEN cnt ELSE 0 END) as oct,
                    MAX( CASE WHEN month = '11' THEN cnt ELSE 0 END) as nov,
                    MAX( CASE WHEN month = '12' THEN cnt ELSE 0 END) as dec
                FROM counts
                GROUP BY task_name, year
                ORDER BY task_name;
    """
    return connexion.execute(query, params).fetchall()


if __name__ == "__main__":
    connexion = db.connect("timer_data.db")

    # MEAN TIME FOR DAYS WITH A TIMER AND ALL DAYS
    # stats = connexion.execute(MEAN_TIME_WORKED_AND_UNWORKED).fetchall()
    # ordered = []
    # ordered.extend(stats[1:])
    # ordered.append(stats[0])
    # ordered_formatted = [
    #     (day, format_time(avg_worked), format_time(avg_unworked))
    #     for day, avg_worked, avg_unworked in ordered
    # ]
    # print(ordered_formatted)

    # MEAN TIME FOR WEEKS WITH TIMER AND EVERY WEEK
    # weeks = connexion.execute(WEEK_MEAN_TIMES).fetchone()
    # print(weeks)
    # avg_worked, avg_all = format_time(weeks[0]), format_time(weeks[1])
    # print(avg_worked, avg_all)
    # stats = connexion.execute(YEAR_IN_TASK).fetchall()
    # formatted_stats = [(task, day_cnt, format_time(time_elapsed, "day")) for (task, day_cnt, time_elapsed) in stats]
    # for r in formatted_stats:
    #    print(f"| {r[0]} | {r[1]} | {r[2]} |")

    # TOTAL TIME FOR EACH YEAR
    # time_year = total_time_for_year()
    # formatted = [(year, format_time(time_elapsed, "day"), ratio) for (year, time_elapsed, ratio) in time_year]
    # for r in formatted:
    #     print(f"| {r[0]} | {r[1]} | {r[2]} |")

    # # TOTAL TIME FOR EACH TASK FOR EACH YEAR
    # task_time_per_year = total_time_for_each_task_for_years()
    # formatted = [(year, task, format_time(time_elapsed, "day"), ratio if ratio else '0') for (year, task, time_elapsed, ratio) in task_time_per_year]
    # for r in formatted:
    #     print(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |")
    # print("----------------------------------------------------")

    # # TOTAL TASK PER DAY OF WEEK
    # task_per_day = count_task_for_each_days(["2022", "2023"])
    # print("| year | task | mon. |tue. | wed. | thu. |  fri. | sat. | sun. |")
    # for row in task_per_day :
    # print(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} | {row[7]} | {row[8]} |")

    # task_per_day_per_month = count_days_with_task_in_month_for_years(["2022", "2023"])
    # print("|year|task_name|jan|feb|mar|apr|may|june|july|aug|sept|oct|nov|dec|")
    # print("|-|-|-|-|-|-|-|-|-|-|-|-|-|-|")
    # for year,task_name,jan,feb,mar,apr,may,june,july,aug,sept,oct,nov,dec in task_per_day_per_month:
    #     print(f"|{year}|{task_name}|{jan}|{feb}|{mar}|{apr}|{may}|{june}|{july}|{aug}|{sept}|{oct}|{nov}|{dec}|")


    #TOTAL TIME PER WEEK
    # ttpw = total_time_per_week(["2023"])
    # formatted_result = [(date, wn, sw, ew, format_time(tt, "hour")) for date, wn, sw, ew, tt in ttpw]
    # print("| year | week_num | start_week | end_week | total time |")
    # print("| :--: | :------: | :--------: | :------: | :--------: |")
    # for date, wn, sw, ew, tt in formatted_result:
        # print(f"| {date} | {wn} | {sw} | {ew} | {tt} |")
    # print(formatted_result)
