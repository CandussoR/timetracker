from sqlite3 import Connection
from typing import List, Literal, Optional
from flask import g
from src.shared.repositories.stats_repository import SqliteStatRepository
from src.shared.utils.format_time import format_time
from datetime import datetime, timedelta
from werkzeug.datastructures import ImmutableMultiDict
import calendar

from src.web_api.services.time_record_service import TimeRecordService


class StatService():
    def __init__(self, connexion : Connection | None = None):
        self.connexion = g._database if connexion == None else connexion
        self.repo = SqliteStatRepository(self.connexion)

    def get_home_stats(self):
        #TODO : Make a decision regarding the way I'm sending time to the front. Array or str ?
        try: 
            mean_week = self.repo.mean_time_per_period("week")
            formatted_mean_week = format_time(mean_week, "day") if mean_week > 86400 else format_time(mean_week, "hour")
            mean_month = self.repo.mean_time_per_period("month")
            formatted_mean_month = format_time(mean_month, "day") if mean_month > 86400 else format_time(mean_month, "hour")
            home = {
                "daily" : {
                    "count": self.repo.timer_count("today"),
                    "time" : format_time(self.repo.total_time("today") or 0, "hour").split(":"),
                    "mean" : format_time(self.repo.mean_time_per_period("day"), "hour").split(":")
                }, 
                "weekly" : {
                    "count": self.repo.timer_count("week"),
                    "time" : format_time(self.repo.total_time("week") or 0, "hour").split(":"),
                    "mean": formatted_mean_week.split(":")
                },
                "monthly" : {
                    "count": self.repo.timer_count("month"),
                    "time" : format_time(self.repo.total_time("month") or 0, "day").split(":"),
                    "mean" : formatted_mean_month.split(":")
                },
                "yearly" : {
                    "count": self.repo.timer_count("year"),
                    "time" : format_time(self.repo.total_time("year") or 0, "day").split(":")
                }
            }
            return home
        except Exception as e:
            raise Exception(e) from e
    

    def get_week_total_time_per_week_for_years(self, years : list[str]):
        '''
            Used to fill a year of week times in a bar chart in the front.
        '''
        try:
            res = self.repo.total_time_per_week_for_years(years)
            years = {year for (year, _, _, _, _) in res}
            obj = {}
            for y in years :
                # Too much coupling with apexcharts
                obj[y] = [{"x": week, "y": time} for (year, week, _, _, time) in res if year == y]
            return obj
        except Exception as e:
            raise Exception(e) from e
    

    def get_task_time_ratio(self, params : dict):
        # Sent from the front only, only period without date in stats/resume
        period = params.get("period")
        if period:
            del params["period"]
            today = datetime.today()
            match(period):
                case "day":
                    params["day"] = today.strftime('%Y-%m-%d')
                case "week":
                    start_of_week = today - timedelta(days=today.weekday())
                    end_of_week = start_of_week + timedelta(days=6)
                    params["weekStart"] = start_of_week.strftime('%Y-%m-%d')
                    params["weekEnd"] = end_of_week.strftime('%Y-%m-%d')
                case "month":
                    params["month"] = today.strftime('%Y-%m')
                case "year":
                    params["year"] = str(today.year)
                case "custom":
                    params["rangeBeginning"], params["rangeEndinging"] = params["custom"]

        res = self.repo.get_task_time_ratio(params)
        if res == None:
            return []
        
        data = []
        for _, task, time, ratio in res:
            if time == None:
                continue
            # if time exceeds a day
            if time > 86400:
               data.append({"task" : task, "time": time, "formatted": format_time(time, 'day'), "ratio" : ratio})
            else :
                data.append({"task" : task, "time": time, "formatted": format_time(time, 'hour'), "ratio" : ratio})
        return data
    
    
    def get_generic_week(self, week_beginning_date : str | None = None):
        # 1.1 Get all the dates for the current week
        # assuming Monday is the start of the week
        today = None
        start_of_week = week_beginning_date
        end_of_week = None

        if not start_of_week :
            today = datetime.today()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
        else :
            first_day = datetime.strptime(week_beginning_date, '%Y-%m-%d')
            start_of_week = first_day - timedelta(days=first_day.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
        days_in_week = self.get_column_dates_for("week", start_of_week)
        time_per_day = self.repo.total_time_per_day_in_range(days_in_week[0], days_in_week[-1])
        len_fill = 7 - len(time_per_day)

        # 1.2. Get task_time_ratio for every day of the week.     
        ratios = self.repo.get_task_time_per_day_between(start_of_week, end_of_week)
        stacked = self.create_apex_bar_chart_object(ratios, days_in_week, len_fill)

        # 2. Total time per day of the week
        days_line_chart = self.create_apex_line_chart_object(time_per_day, len_fill)

        return {"dates" : days_in_week, "stackedBarChart" : stacked, "daysLineChart": days_line_chart}
    

    def get_generic_month(self, month : datetime | None = None):
        # Get task_time_ratio for every day of the week.
        month = month

        if not month :
            month = datetime.now().replace(day=1)

        weeks = self.get_column_dates_for("month", month)
        week_times = self.repo.total_time_per_week_in_range(str(month.year), weeks[0], weeks[-1])
        len_fill = len(weeks) - len(week_times)

        # Graph stacked column chart
        ratios = self.repo.get_task_time_per_week_in_month(month)
        stacked = self.create_apex_bar_chart_object(ratios, weeks, len_fill)

        # Total time per week of the month
        week_line_chart = self.create_apex_line_chart_object(week_times, len_fill)

        return {"weeks" : weeks, "stackedBarChart" : stacked, "weeksLineChart": week_line_chart }


    def get_generic_year(self, year : datetime | None = None):
        # 1.2. Get task_time_ratio for every month of year.
        year = year
        if year is None:
            year = datetime.strptime(str(datetime.now().year), '%Y')

        ratios = (self.repo.get_task_time_per_month_in_year(year))
        
        months = self.get_column_dates_for("year", year)
        time_per_month = self.repo.total_time_per_month_in_range(months[0], months[-1])
        len_fill = 12 - len(time_per_month)
        
        stacked = self.create_apex_bar_chart_object(ratios, months, len_fill)

        # # 2. Total time per month of year
        line = self.create_apex_line_chart_object(time_per_month, len_fill)

        return {"months" : months, 
                "stackedBarChart" : stacked, 
                "monthsLineChart": line, 
                "weekLineChart": self.get_week_total_time_per_week_for_years([str(year.year)])}
    

    def get_custom_stats(self, params : ImmutableMultiDict):
        '''
            possible keys in the params dict :
                "day", "week", "year", "month", "rangeBeginning", "rangeEnding", "task", "subtask", "tag", "logs", "logSearch".
        '''
        response_object = {}
        time_format = '%Y-%m-%d'

        # Converting ImmutableMultiDict to dict for the rest of the query
        conditions = {}
        for k in params :
            if k == "week[]":
                continue
            else:
                conditions[k] = params[k]
        if "week[]" in params:
            # keeping the camel case to go with rangeBeginning etc.
            # we don't do bindings but fstrings for the stats repo, so...
            [conditions["weekStart"], conditions["weekEnd"]] = params.getlist("week[]")

        # If normal period, just call the generic function for that period, with specific date :
        keys = conditions.keys()

        if "stats" in keys:
            for i, item in enumerate(conditions["stats"]):
                time_units = []
                ratios = []
                fill = []
                match(item["element"]):
                    case('line-chart'):
                        response_object["stats"][i] = self.create_apex_line_chart_object()
                    case('stacked-column-chart'):
                        ratios = self.get_task_time_ratio(params)
                        response_object["stats"][i]= self.create_apex_bar_chart_object()
                    case('task-ratio'):
                        response_object["stats"][i]= self.get_task_time_ratio(conditions)
                    case('subtask-ratio'):
                        response_object["stats"][i] = self.repo.get_subtask_time_ratio(conditions)
                    case('_'):
                        raise ValueError("Wrong value for stat element.")
        else:
            if "day" in keys:
                print("do sth")
            elif "weekStart" in keys or "weekEnd" in keys:
                response_object["stats"] = self.get_generic_week(conditions["weekStart"])
            elif "month" in keys:
                response_object["stats"] = self.get_generic_month(conditions["month"])
            elif "year" in keys:
                response_object["stats"] = self.get_generic_year(conditions["year"])
            elif "rangeBeginning" in keys:
                if not "rangeEnding" in keys:
                    conditions["rangeEnding"] = datetime.today().strftime(time_format)

                    days_in_range = datetime.strptime(conditions["rangeEnding"], time_format) - datetime.strptime(conditions["rangeBeginning"], time_format)
                    days_in_range = int(days_in_range.total_seconds() / 86400)
                    if days_in_range > 1 and days_in_range < 7:
                        print("get a week-like stats bro")
                        # Get task_time_ratio
                        # Get chart for multiple days
                        # Get bar line for times per day, I guess.
                    elif days_in_range > 7 and days_in_range <= 31:
                        print("get a monthlike thing")
                    else:
                        print("get a year-like graph maybe ? dunno")
                    response_object["stats"] = "yeah it's custom but it's not out yet"   

        if "logs" in keys:
            time_record_service = TimeRecordService()
            response_object["logs"] = time_record_service.get_by(params)        
        
        return response_object
    
    def create_apex_bar_chart_object(self, ratios : list, time_unit_array : list, fill : int):
        '''
            Format data object for apexcharts StackedBar in front.
        '''
        # Makes a list of the set of tasks so we can get an index
        tasks = list({t for _,t,_,_,_ in ratios})
        # Creating an object with values prefilled for each day of the week
        stacked = [{"name" : t, "data" : [0] * ( len(time_unit_array) + fill )} for t in tasks]
        
        for date, task, _, _, ratio in ratios:
            stacked[tasks.index(task)]["data"][time_unit_array.index(date)] = ratio

        return stacked
    

    def create_apex_line_chart_object(self, times : list[str], fill : int):
        '''
            Format data object for apexcharts LineBar in front.
        '''
        line = {"name" : "Total time", "data" : [time for _,time in times]}
        line["data"].extend([None] * fill)
        return line
    

    def get_column_dates_for(self, period : str|int, date : datetime = None ) -> list:
        '''
            Returns an array of dates or ints destined to be placeholders for graphs x abscissa.
        '''
        now = datetime.now()

        match (period):

            case "year":
                year = date.year or now.year
                return [f"{year}-{month:02d}" for month in range(1, now.month+1)]
            
            case "month":
                if date is None :
                    _, first_week_of_month, _ = datetime.strptime(f'{now.year}-{now.month}-01', '%Y-%m-%d').isocalendar()
                    _,last_day = calendar.monthrange(now.year, now.month)
                    _, last_week, _ = datetime(now.year, now.month, last_day).isocalendar()
                else :
                    _, first_week_of_month, _ = date.isocalendar()
                    _,last_day = calendar.monthrange(date.year, date.month)
                    _, last_week, _ = datetime(date.year, date.month, last_day).isocalendar()
                return [f'{week:02d}' for week in range(first_week_of_month, last_week+1)]
            
            case "week":
                if date is None :
                    start_of_week = now - timedelta(days=now.weekday())
                else :
                    start_of_week = date - timedelta(days=date.weekday())
                return [*map(lambda x : x.strftime('%Y-%m-%d'), [start_of_week + timedelta(days=i) for i in range(7)])]