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
    

    def get_week_total_time(self, params : dict):
        try:
            if "years[]" in params.keys():
                res = self.repo.total_time_per_week([params["years[]"]])
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
    
    
    def get_generic_week(self, week_dates : str | None = None):
        # 1.1 Get all the dates for the current week
        # assuming Monday is the start of the week
        today = None
        start_of_week = None
        end_of_week = None

        if not week_dates :
            today = datetime.today()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
        else :
            first_day = datetime.strptime(week_dates, '%Y-%m-%d')
            start_of_week = first_day - timedelta(days=first_day.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
        days_in_week = [*map(lambda x : x.strftime('%Y-%m-%d'), [start_of_week + timedelta(days=i) for i in range(7)])]
        time_per_day = self.repo.total_time_per_day_in_range(days_in_week[0], days_in_week[-1])
        len_fill = 7 - len(time_per_day)

        # 1.2. Get task_time_ratio for every day of the week.     
        ratios = self.repo.get_task_time_per_day_between(start_of_week, end_of_week)
        stacked = self.create_apex_bar_chart_object(ratios, days_in_week, len_fill)

        # 2. Total time per day of the week
        days_line_chart = self.create_apex_line_chart_object(time_per_day, len_fill)

        return {"dates" : days_in_week, "stackedBarChart" : stacked, "daysLineChart": days_line_chart}
    

    def get_generic_month(self, month : str | None = None):
        # Get task_time_ratio for every day of the week.
        month = month
        if not month :
            now = datetime.now()
            month = now.strftime('%Y-%m')
            number_of_weeks = len(calendar.monthcalendar(now.year, now.month))
        else :
           y, m = map(lambda x : int(x), month.split("-"))
           number_of_weeks = len(calendar.monthcalendar(y, m))

        ratios = self.repo.get_task_time_per_week_in_month(month)
        print(ratios)
        # Calculate fill to scale graphs
        weeks = sorted(list({w for w,_,_,_,_ in ratios}))
        week_times = self.repo.total_time_per_week_in_range(weeks[0], weeks[-1])
        len_fill = number_of_weeks - len(week_times)

        # Graph stacked column chart
        stacked = self.create_apex_bar_chart_object(ratios, weeks, len_fill)

        # Total time per week of the month
        week_line_chart = self.create_apex_line_chart_object(week_times, len_fill)

        return {"weeks" : weeks, "stackedBarChart" : stacked, "weeksLineChart": week_line_chart }


    def get_generic_year(self, year : str | None = None):
        # 1.2. Get task_time_ratio for every month of year.
        year = year
        if year is None:
            now = datetime.now()
            year = now.strftime('%Y')

        ratios = (self.repo.get_task_time_per_month_in_year(year))
        
        months = self.get_column_dates("year")
        time_per_month = self.repo.total_time_per_month_in_range(months[0], months[-1])
        len_fill = 12 - len(time_per_month)
        
        stacked = self.create_apex_bar_chart_object(ratios, months, len_fill)

        # # 2. Total time per month of year
        line = self.create_apex_line_chart_object(time_per_month, len_fill)

        return {"months" : months, 
                "stackedBarChart" : stacked, 
                "monthsLineChart": line, 
                "weekLineChart": self.get_week_total_time({"years[]" : year})}
    

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
    

    def get_column_dates(self, period : str|int ) -> list:
        match (period):
            case "year":
                now = datetime.now()
                year = now.strftime('%Y')
                months = [f"{year}-{month:02d}" for month in range(1, now.month+1)]
                return months
            case "month":
                now = datetime.now()
                month = now.strftime('%Y-%m')
                number_of_weeks = len(calendar.monthcalendar(now.year, now.month))
                return 