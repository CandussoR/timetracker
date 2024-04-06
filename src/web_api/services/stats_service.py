from sqlite3 import Connection
from typing import List, Literal, Optional
from flask import g
from src.shared.repositories.stats_repository import SqliteStatRepository
from src.shared.utils.custom_dict_converter import convert_to_custom_dict
from src.shared.utils.format_time import format_time
from datetime import datetime, timedelta
from werkzeug.datastructures import ImmutableMultiDict
import calendar

from src.web_api.services.time_record_service import TimeRecordService


class StatService():
    def __init__(self, connexion : Connection | None = None, request : ImmutableMultiDict | None = None):
        self.connexion = g._database if connexion == None else connexion
        self.repo = SqliteStatRepository(self.connexion)
        self.request = convert_to_custom_dict(request) if request else None
        self.period_stat = self.create_stat_object(self.request)
    

    def create_stat_object(self, request_dict : dict):
        '''
            Factory based on the dictionary transformed from the front request.
        '''
        print(request_dict)
        if request_dict is None: return None
        haystack = request_dict.get("period")
        if not haystack :
            haystack = request_dict.keys()
        if "day" in haystack:
            return DayStat()
        elif "week" in haystack or "weekStart" in haystack:
            return WeekStat()
        elif "month" in haystack:
            return MonthStat()
        elif "year" in haystack :
            return YearStat()

    def ggs(self, date : datetime):
        # prb with the request argument : should be modular depending on what object is created.
        return self.period_stat.get_generic_stat(self.repo, date)

    def get_home_stats(self):
        '''
            Getting home start for everywhere at once.
        '''
        return {
            "daily" : DayStat().get_home_stat(self.repo), 
            "weekly" : WeekStat().get_home_stat(self.repo),
            "monthly" : MonthStat().get_home_stat(self.repo),
            "yearly" : YearStat().get_home_stat(self.repo)
        }
    

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
        '''
            There's a little quirk here : if a week already set is to be passed, the dict must be of type `{"weekStart" : dt, "weekEnd" : dt}`.
            Otherwise, we take a specified period and do our little thing, and week is transformed in said way.
        '''
        # Sent from the front only, only period without date in stats/resume
        if period := params.get("period"):
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
    
    
    def get_generic_week(self, week_beginning_date : str | datetime | None = None):
        # 1.1 Get all the dates for the current week
        # assuming Monday is the start of the week
        # if not week_beginning_date :
        #     week_beginning_date = datetime.today()
        # if isinstance(week_beginning_date, str):
        #     week_beginning_date = datetime.strptime(week_beginning_date, '%Y-%m-%d')
        # start_of_week = week_beginning_date - timedelta(days=week_beginning_date.weekday())
        # end_of_week = start_of_week + timedelta(days=6)
            
        # days_in_week = self.get_column_dates_for("week", start_of_week)
        # time_per_day = self.repo.total_time_per_day_in_range(days_in_week[0], days_in_week[-1])
        # len_fill = 7 - len(time_per_day)

        # # 1.2. Get task_time_ratio for every day of the week.     
        # ratios = self.repo.get_task_time_per_day_between(start_of_week, end_of_week)
        # stacked = self.create_apex_bar_chart_object(ratios, days_in_week, len_fill)

        # # 2. Total time per day of the week
        # days_line_chart = self.create_apex_line_chart_object(time_per_day, len_fill)

        # return {"dates" : days_in_week, "stackedBarChart" : stacked, "daysLineChart": days_line_chart}
        self.ggs(week_beginning_date)
    

    def get_generic_month(self, month : datetime | None = None):
        '''
            Gets a datetime object "YYYY-MM-DD" and returns a dict with :
            `weeks` : the week numbers of the month,
            `stackedBarChart` : data formated for Apex Charts Stacked Bar Chart,
            `weeksLineChart` : date formated for Apex Charts Line Chart.
        '''
        # Get task_time_ratio for every day of the week.
        if isinstance(month, str):
            month = datetime.strptime(month, '%Y-%m')
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
        if year is None:
            year = datetime.now()

        ratios = self.repo.get_task_time_per_month_in_year(year)
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

        # # If normal period, just call the generic function for that period, with specific date :
        conditions = convert_to_custom_dict(params)
        keys = conditions.keys()

        if "stats" in keys:
            for i, item in enumerate(conditions["stats"]):
                match(item["element"]):
                    case('line-chart'):
                        response_object["stats"][i] = self.create_apex_line_chart_object()
                    case('stacked-column-chart'):
                        ratios = self.get_task_time_ratio(params)
                        time_unit_array = self.get_column_dates_for(item["period"])
                        response_object["stats"][i]= self.create_apex_bar_chart_object(ratios, time_unit_array)
                    case('task-ratio'):
                        response_object["stats"][i]= self.get_task_time_ratio(conditions)
                    case('subtask-ratio'):
                        response_object["stats"][i] = self.repo.get_subtask_time_ratio(conditions)
                    case('_'):
                        raise ValueError("Wrong value for stat element.")

        if "day" in keys:
            print("do sth")
        elif "weekStart" in keys or "weekEnd" in keys:
            response_object["generic"] = self.get_generic_week(conditions["weekStart"])
        elif "month" in keys:
            response_object["generic"] = self.get_generic_month(conditions["month"])
        elif "year" in keys:
            response_object["generic"] = self.get_generic_year(conditions["year"])
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
        if date is None:
            date = datetime.now()

        match (period):
            case "year":
                return [f"{date.year}-{month:02d}" for month in range(1, datetime.now().month+1)]
            
            case "month":
                _, first_week_of_month, _ = date.isocalendar()
                _,last_day = calendar.monthrange(date.year, date.month)
                _, last_week, _ = datetime(date.year, date.month, last_day).isocalendar()
                return [f'{week:02d}' for week in range(first_week_of_month, last_week+1)]
            
            case ("week"):
                start_of_week = date - timedelta(days=date.weekday())
                return [*map(lambda x : x.strftime('%Y-%m-%d'), [start_of_week + timedelta(days=i) for i in range(7)])]


class DayStat():

    def get_home_stat(self, repo : SqliteStatRepository):
        return  {
                "count": repo.timer_count("today"),
                "time" : format_time(repo.total_time("today") or 0, "hour").split(":"),
                "mean" : format_time(repo.mean_time_per_period("day"), "hour").split(":")
                }

    def get_generic_stat(self) :
        raise NotImplementedError("This function does not exist for this period.")


class WeekStat():

    def get_home_stat(self, repo : SqliteStatRepository):
        mean_week = repo.mean_time_per_period("week")
        formatted_mean_week = format_time(mean_week, "day") if mean_week > 86400 else format_time(mean_week, "hour")
        return {
                    "count": repo.timer_count("week"),
                    "time" : format_time(repo.total_time("week") or 0, "hour").split(":"),
                    "mean": formatted_mean_week.split(":")
                }


    def get_generic_stat(self, repo : SqliteStatRepository, week_beginning_date : datetime | None = None) :
        # 1.1 Get all the dates for the current week
        # assuming Monday is the start of the week
        if not week_beginning_date :
            week_beginning_date = datetime.today()
        if isinstance(week_beginning_date, str):
            week_beginning_date = datetime.strptime(week_beginning_date, '%Y-%m-%d')

        start_of_week = week_beginning_date - timedelta(days=week_beginning_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
            
        days_in_week = self.get_column_dates(start_of_week)
        time_per_day = repo.total_time_per_day_in_range(days_in_week[0], days_in_week[-1])
        len_fill = 7 - len(time_per_day)

        # 1.2. Get task_time_ratio for every day of the week.     
        ratios = repo.get_task_time_per_day_between(start_of_week, end_of_week)
        stacked = self.create_apex_bar_chart_object(ratios, days_in_week, len_fill)

        # 2. Total time per day of the week
        days_line_chart = self.create_apex_line_chart_object(time_per_day, len_fill)

        return {"dates" : days_in_week, "stackedBarChart" : stacked, "daysLineChart": days_line_chart}


    def get_column_dates(self, date : datetime | None = None):
        start_of_week = date - timedelta(days=date.weekday())
        return [*map(lambda x : x.strftime('%Y-%m-%d'), [start_of_week + timedelta(days=i) for i in range(7)])] 
    

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

    
class MonthStat():
    def get_home_stat(self, repo : SqliteStatRepository):
        mean_month = repo.mean_time_per_period("month")
        formatted_mean_month = format_time(mean_month, "day") if mean_month > 86400 else format_time(mean_month, "hour")
        return {
                    "count": repo.timer_count("month"),
                    "time" : format_time(repo.total_time("month") or 0, "day").split(":"),
                    "mean" : formatted_mean_month.split(":")
                }
    

    def get_generic_stat(self) :
        pass 


    def get_column_date(self, date : datetime | None = None):
        _, first_week_of_month, _ = date.isocalendar()
        _,last_day = calendar.monthrange(date.year, date.month)
        _, last_week, _ = datetime(date.year, date.month, last_day).isocalendar()
        return [f'{week:02d}' for week in range(first_week_of_month, last_week+1)]

class YearStat():
    def get_home_stat(self, repo : SqliteStatRepository):
        return {
                    "count": repo.timer_count("year"),
                    "time" : format_time(repo.total_time("year") or 0, "day").split(":")
                }

    def get_generic_stat(self) :
        pass

    def get_column_date(self, date : datetime | None = None):
        return [f"{date.year}-{month:02d}" for month in range(1, datetime.now().month+1)]