from sqlite3 import Connection
from typing import Optional
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
        '''
           params can be `{"period" : year|month|week|day, "date" : string, list[str], None}`
           or at least one param.
           Returns the total time and ratio for a task during a certain period.
        '''
        date = params.get("date")

        if date is None :
            today = datetime.today()
            match(params["period"]):
                case "day":
                    params["date"] = today.strftime('%Y-%m-%d')
                case "week":
                    start_of_week = today - timedelta(days=today.weekday())
                    params["date"] = start_of_week.strftime('%Y-%m-%d')
                case "month":
                    params["date"] = today.strftime('%Y-%m')
                case "year":
                    params["date"] = str(today.year)
        elif isinstance(date, list):
            params["rangeBeginning"], params["rangeEnding"] = date
            del params["date"]

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
        if not week_dates :
            today = datetime.today()
            start_of_week = today - timedelta(days=today.weekday())
        else :
            start_of_week = datetime.strptime(week_dates[0], '%Y-%m-%d')
        days_in_week = [start_of_week + timedelta(days=i) for i in range(7)]
        days_in_week = [*map(lambda x : x.strftime('%Y-%m-%d'), days_in_week)]

        # 1.2. Get task_time_ratio for every day of the week.
        ratios = []
        for d in days_in_week:
            ratios.append(self.repo.get_task_time_ratio({"period": "day", "date": d}))

        # Too much coupling with apexcharts ?
        # 1.3. Format data object for apexcharts loading StackedBar with VueJs 
        unique_tasks = {task for r in ratios for _, task, _, _ in r}
        # 1.3.2. Creating an object with values prefilled for each day
        stacked = []
        for t in unique_tasks:
            stacked.append({"name" : t, "data" : [0] * 7})
        stacked_tasks = [obj["name"] for obj in stacked]

        for sublist in ratios:
            for item in sublist:
                index = stacked_tasks.index(item[1])
                stacked[index]["data"][ratios.index(sublist)] = item[3]

        # 2. Total time per day of the week
        days_line_chart = self.repo.total_time_per_day_in_range(days_in_week[0], days_in_week[-1])
        days_line_chart = {"name" : "Total time", "data" : [time for _,time in days_line_chart]}
        len_fill = 7 - len(days_line_chart["data"])
        if len_fill:
            days_line_chart["data"].extend([None] * len_fill)

        return {"dates" : days_in_week, "stackedBarChart" : stacked, "daysLineChart": days_line_chart}
    

    def get_generic_month(self, month : str | None = None):
        # 1.2. Get task_time_ratio for every day of the week.
        month = month
        if not month :
            now = datetime.now()
            month = now.strftime('%Y-%m')
            number_of_weeks = len(calendar.monthcalendar(now.year, now.month))
        else :
           y, m = month.split("-")
           number_of_weeks = len(calendar.monthcalendar(y, m)) 

        ratios = []
        ratios.extend(self.repo.get_task_time_per_week_in_month(month))

        weeks = sorted(list({w for w,_,_,_,_ in ratios}))  
        tasks = {t for _,t,_,_,_ in ratios}

        stacked = []
        for t in tasks:
            stacked.append({"name" : t, "data" : [0] * number_of_weeks})
        for week,task,_,_,ratio in ratios:
            i_week = [i for i, w in enumerate(weeks) if w == week][0]
            i_task = [i for i, t in enumerate(tasks) if t == task][0]
            stacked[i_task]["data"][i_week] = ratio

        # # 2. Total time per week of the month
        weeks = list(weeks)
        weeks_line_chart = self.repo.total_time_per_week_in_range(weeks[0], weeks[-1])
        weeks_line_chart = {"name" : "Total time", "data" : [time for _,time in weeks_line_chart]}
        len_fill = number_of_weeks - len(weeks_line_chart["data"])
        if len_fill:
            weeks_line_chart["data"].extend([None] * len_fill)

        return {"weeks" : weeks, "stackedBarChart" : stacked, "weeksLineChart": weeks_line_chart }


    def get_generic_year(self, year : str | None = None):
        # 1.2. Get task_time_ratio for every month of year.
        year = year
        if year is None:
            now = datetime.now()
            year = now.strftime('%Y')

        ratios = []
        ratios.extend(self.repo.get_task_time_per_month_in_year(year))

        months = sorted(list({m for m,_,_,_,_ in ratios}))  
        tasks = {t for _,t,_,_,_ in ratios}

        stacked = []
        for t in tasks:
            stacked.append({"name" : t, "data" : [0] * 12})
        for month,task,_,_,ratio in ratios:
            i_month = [i for i, m in enumerate(months) if m == month][0]
            i_task = [i for i, t in enumerate(tasks) if t == task][0]
            stacked[i_task]["data"][i_month] = ratio

        # # 2. Total time per month of year
        month = list(months)
        months_line_chart = self.repo.total_time_per_month_in_range(month[0], month[-1])
        months_line_chart = {"name" : "Total time", "data" : [time for _,time in months_line_chart]}
        len_fill = 12 - len(months_line_chart["data"])
        if len_fill:
            months_line_chart["data"].extend([None] * len_fill)

        return {"months" : months, 
                "stackedBarChart" : stacked, 
                "monthsLineChart": months_line_chart, 
                "weekLineChart": self.get_week_total_time({"years[]" : year})}
    

    # Should this be a builder ?
    def get_custom_stats(self, params : ImmutableMultiDict):
        '''
            possible keys in the params dict :
                "day", "week", "year", "month", "rangeBeginning", "rangeEnd", "task", "subtask", "tag", "logs", "logSearch".
        '''
        response_object = {}
        time_format = '%Y-%m-%d'

        # If logs, getting the TimeRecords with the ImmutableMultiDict
        if "log" in params.keys():
            tr_service = TimeRecordService()
            response_object["records"] = tr_service.get_by(params.keys())

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
        if "subtask" in keys and not "task" in keys:
            return ValueError("Missing a task.")
        
        if ("task" in keys) or ("tag" in keys):
            # Trouver le temps total pour la tâche
            # Peut-être trouver le temps total consacré à la sous-tâche par rapport au temps total consacrée à la tâche.
            if "tag" in keys or not "subtask" in keys:
                response_object["stats"] = self.repo.get_subtask_time(conditions)
            elif "subtask" in keys:
                response_object["stats"] = "we should just get the task and maybe how much of the time overall it counts for"
                print("task and subtask but not tags indeed")

        elif (set(["day", "weekStart", "weekEnd" "month", "year"]).issubset(keys)
            and not set(["task", "subtask", "tag"]).issubset(keys)):
            if "day" in keys:
                print("do sth")
            elif "weekStart" in keys or "weekEnd" in keys:
                response_object["stats"] = self.get_generic_week(conditions["weekStart"])
            elif "month" in keys:
                response_object["stats"] = self.get_generic_month(conditions["month"])
            elif "year" in keys:
                response_object["stats"] = self.get_generic_year(conditions["year"])
            elif "rangeBeginning" in keys:
                if not "rangeEnd" in keys:
                    conditions["rangeEnd"] = datetime.today().strftime(time_format)

                days_in_range = datetime.strptime(conditions["rangeEnd"], time_format) - datetime.strptime(conditions["rangeBeginning"], time_format)
                days_in_range = int(days_in_range.total_seconds() / 86400)
                if days_in_range > 1 and days_in_range < 7:
                    print("get a week-like stats bro")
                elif days_in_range > 7 and days_in_range <= 31:
                    print("get a monthlike thing")
                else:
                    print("get a year-like graph maybe ? dunno")
                response_object["stats"] = "yeah it's custom but it's not out yet"   

        if "logs" in keys and conditions["logs"]:
            time_record_service = TimeRecordService()
            response_object["logs"] = time_record_service.get_by(params)        
        
        return response_object

