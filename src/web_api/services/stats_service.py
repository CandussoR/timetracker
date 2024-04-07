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
 

class BaseStatService():
    def __init__(self, connexion : Connection | None = None, request : ImmutableMultiDict | None = None):
        self.connexion = g._database if connexion == None else connexion
        self.repo = SqliteStatRepository(self.connexion)
        self.request = convert_to_custom_dict(request) if request else None
    

    def get_home_stats(self):
        '''
            Getting home start for everywhere at once.
        '''
        return {
            "daily" : DayStatService(self.connexion).get_home_stat(),
            "weekly" : WeekStatService(self.connexion).get_home_stat(),
            "monthly" : MonthStatService(self.connexion).get_home_stat(),
            "yearly" : YearStatService(self.connexion).get_home_stat()
        }
    

    def get_task_time_ratio(self):
        '''
            There's a little quirk here : if a week already set is to be passed, the dict must be of type `{"weekStart" : dt, "weekEnd" : dt}`.
            Otherwise, we take a specified period and do our little thing, and week is transformed in said way.
        '''

        res = self.repo.get_task_time_ratio(self.request)
        print(res)
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
    

    # def get_custom_stats(self, params : ImmutableMultiDict):
    #     '''
    #         possible keys in the params dict :
    #             "day", "week", "year", "month", "rangeBeginning", "rangeEnding", "task", "subtask", "tag", "logs", "logSearch".
    #     '''
    #     response_object = {}
    #     time_format = '%Y-%m-%d'

    #     # # If normal period, just call the generic function for that period, with specific date :
    #     conditions = convert_to_custom_dict(params)
    #     keys = conditions.keys()

    #     if "stats" in keys:
    #         for i, item in enumerate(conditions["stats"]):
    #             match(item["element"]):
    #                 case('line-chart'):
    #                     response_object["stats"][i] = self.create_apex_line_chart_object()
    #                 case('stacked-column-chart'):
    #                     ratios = self.get_task_time_ratio(params)
    #                     time_unit_array = self.get_column_dates_for(item["period"])
    #                     response_object["stats"][i]= self.create_apex_bar_chart_object(ratios, time_unit_array)
    #                 case('task-ratio'):
    #                     response_object["stats"][i]= self.get_task_time_ratio(conditions)
    #                 case('subtask-ratio'):
    #                     response_object["stats"][i] = self.repo.get_subtask_time_ratio(conditions)
    #                 case('_'):
    #                     raise ValueError("Wrong value for stat element.")

    #     if "day" in keys:
    #         print("do sth")
    #     elif "weekStart" in keys or "weekEnd" in keys:
    #         response_object["generic"] = self.get_generic_week(conditions["weekStart"])
    #     elif "month" in keys:
    #         response_object["generic"] = self.get_generic_month(conditions["month"])
    #     elif "year" in keys:
    #         response_object["generic"] = self.get_generic_year(conditions["year"])
    #     elif "rangeBeginning" in keys:
    #         if not "rangeEnding" in keys:
    #             conditions["rangeEnding"] = datetime.today().strftime(time_format)

    #         days_in_range = datetime.strptime(conditions["rangeEnding"], time_format) - datetime.strptime(conditions["rangeBeginning"], time_format)
    #         days_in_range = int(days_in_range.total_seconds() / 86400)
    #         if days_in_range > 1 and days_in_range < 7:
    #             print("get a week-like stats bro")
    #             # Get task_time_ratio
    #             # Get chart for multiple days
    #             # Get bar line for times per day, I guess.
    #         elif days_in_range > 7 and days_in_range <= 31:
    #             print("get a monthlike thing")
    #         else:
    #             print("get a year-like graph maybe ? dunno")
    #             response_object["stats"] = "yeah it's custom but it's not out yet"   

    #     if "logs" in keys:
    #         time_record_service = TimeRecordService()
    #         response_object["logs"] = time_record_service.get_by(params)        
        
    #     return response_object
    
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


class DayStatService(BaseStatService):
    def __init__(self, connexion : Optional[Connection], request: Optional[ImmutableMultiDict] = None):
        super().__init__(connexion, request)

    def get_home_stat(self):
        return  {
                "count": self.repo.timer_count("today"),
                "time" : format_time(self.repo.total_time("today") or 0, "hour").split(":"),
                "mean" : format_time(self.repo.mean_time_per_period("day"), "hour").split(":")
                }


    def get_task_time_ratio(self):
        if not "period" in self.request or not "day" in self.request: 
            self.request["day"] = datetime.now().strftime("%Y-%m-%d")
        return super().get_task_time_ratio()
    

    def get_generic_stat(self) :
        raise NotImplementedError("This function does not exist for this period.")


class WeekStatService(BaseStatService):
    def __init__(self, connexion : Optional[Connection], request: Optional[ImmutableMultiDict] = None):
        super().__init__(connexion, request)


    def get_home_stat(self):
        mean_week = self.repo.mean_time_per_period("week")
        formatted_mean_week = format_time(mean_week, "day") if mean_week > 86400 else format_time(mean_week, "hour")
        return {
                    "count": self.repo.timer_count("week"),
                    "time" : format_time(self.repo.total_time("week") or 0, "hour").split(":"),
                    "mean": formatted_mean_week.split(":")
                }


    def get_task_time_ratio(self):
        '''
            Get task_time_ratio according to the request passed : either with period, or with pair weekStart and weekEnd.
        '''
        if "period" in self.request:
            self.request["weekStart"], self.request["weekEnd"] = map(lambda x : x.strftime("%Y-%m-%d"), self._get_week_range())
        return super().get_task_time_ratio()
    

    def get_generic_stat(self, week_beginning_date : datetime | None = None) :
        # 1.1 Get all the dates for the current week
        # assuming Monday is the start of the week
        if not week_beginning_date :
            week_beginning_date = datetime.today()
        if isinstance(week_beginning_date, str):
            week_beginning_date = datetime.strptime(week_beginning_date, '%Y-%m-%d')

        start_of_week, end_of_week = self._get_week_range(week_beginning_date)
            
        days_in_week = self.get_column_dates(start_of_week)
        time_per_day = self.repo.total_time_per_day_in_range(days_in_week[0], days_in_week[-1])
        len_fill = 7 - len(time_per_day)

        # 1.2. Get task_time_ratio for every day of the week.     
        ratios = self.repo.get_task_time_per_day_between(start_of_week, end_of_week)
        stacked = super().create_apex_bar_chart_object(ratios, days_in_week, len_fill)

        # 2. Total time per day of the week
        days_line_chart = super().create_apex_line_chart_object(time_per_day, len_fill)

        return {"dates" : days_in_week, "stackedBarChart" : stacked, "daysLineChart": days_line_chart}


    def get_column_dates(self, date : datetime | None = None):

        start_of_week = date - timedelta(days=date.weekday())
        return [*map(lambda x : x.strftime('%Y-%m-%d'), [start_of_week + timedelta(days=i) for i in range(7)])] 
    

    def _get_week_range(self, a_date : Optional[datetime] = None):
        '''
            Return the first and last day of the week.
        '''
        today = datetime.now() if not a_date else a_date
        weekday = today.weekday()
        return (today - timedelta(days=weekday)), (today + timedelta(days=6 - weekday))

    
class MonthStatService(BaseStatService):
    def __init__(self, connexion : Optional[Connection], request: Optional[ImmutableMultiDict] = None):
        super().__init__(connexion, request)


    def get_home_stat(self):
        mean_month = self.repo.mean_time_per_period("month")
        formatted_mean_month = format_time(mean_month, "day") if mean_month > 86400 else format_time(mean_month, "hour")
        return {
                    "count": self.repo.timer_count("month"),
                    "time" : format_time(self.repo.total_time("month") or 0, "day").split(":"),
                    "mean" : formatted_mean_month.split(":")
                }
    

    def get_task_time_ratio(self):
        if "period" in self.request and not "month" in self.request:
            self.request["month"] = datetime.now()
        self.request["month"]= self.request["month"].strftime('%Y-%m')
        return super().get_task_time_ratio()


    def get_generic_stat(self, month : datetime | str = None) -> dict:
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

        weeks = self.get_column_dates(month)
        week_times = self.repo.total_time_per_week_in_range(str(month.year), weeks[0], weeks[-1])
        len_fill = len(weeks) - len(week_times)

        # Graph stacked column chart
        ratios = self.repo.get_task_time_per_week_in_month(month)
        stacked = super().create_apex_bar_chart_object(ratios, weeks, len_fill)

        # Total time per week of the month
        week_line_chart = super().create_apex_line_chart_object(week_times, len_fill)

        return {"weeks" : weeks, "stackedBarChart" : stacked, "weeksLineChart": week_line_chart }


    def get_column_dates(self, date : datetime | None = None):
        _, first_week_of_month, _ = date.isocalendar()
        _,last_day = calendar.monthrange(date.year, date.month)
        _, last_week, _ = datetime(date.year, date.month, last_day).isocalendar()
        return [f'{week:02d}' for week in range(first_week_of_month, last_week+1)]


class YearStatService(BaseStatService):
    def __init__(self, connexion : Optional[Connection], request: Optional[ImmutableMultiDict] = None):
        super().__init__(connexion, request)

    def get_home_stat(self):
        return {
                    "count": self.repo.timer_count("year"),
                    "time" : format_time(self.repo.total_time("year") or 0, "day").split(":")
                }

    def get_task_time_ratio(self):
        if "period" in self.request and not "year" in self.request:
            self.request["year"] = datetime.now()
        self.request["year"]= self.request["year"].strftime('%Y')
        return super().get_task_time_ratio()
    
    def get_generic_stat(self, year : datetime) :
        # 1.2. Get task_time_ratio for every month of year.
        if year is None:
            year = datetime.now()

        ratios = self.repo.get_task_time_per_month_in_year(year)
        months = self.get_column_dates(year)
        time_per_month = self.repo.total_time_per_month_in_range(months[0], months[-1])
        len_fill = 12 - len(time_per_month)
        
        stacked = super().create_apex_bar_chart_object(ratios, months, len_fill)

        # # 2. Total time per month of year
        line = super().create_apex_line_chart_object(time_per_month, len_fill)

        return {"months" : months, 
                "stackedBarChart" : stacked, 
                "monthsLineChart": line, 
                "weekLineChart": self.get_week_total_time_per_week_for_years([str(year.year)])}


    def get_column_dates(self, date : datetime | None = None):
        return [f"{date.year}-{month:02d}" for month in range(1, datetime.now().month+1)]
    
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
        

class StatServiceFactory():
    '''
        Factory that creates the service depending on a "period" key or a time span key (day, weekStart, month, year).
    '''
    @staticmethod
    def create_stat_service(connexion: Optional[Connection] = None, request: Optional[ImmutableMultiDict] = None) -> BaseStatService:
        connexion = g._database if connexion is None else connexion
        request_dict = convert_to_custom_dict(request) if request else None
        
        init_attributes = {"connexion" : connexion, "request": request}
        service = StatServiceFactory.create_stat_object(request_dict, init_attributes)
        return service
    
    @staticmethod
    def create_stat_object(request_dict: dict, init_attributes: dict) -> DayStatService|WeekStatService|MonthStatService|YearStatService|None:
        if request_dict is None:
            return BaseStatService(**init_attributes)

        haystack = request_dict.get("period")
        if not haystack:
            haystack = request_dict.keys()

        if "day" in haystack:
            return DayStatService(**init_attributes)
        elif "week" in haystack or "weekStart" in haystack:
            return WeekStatService(**init_attributes)
        elif "month" in haystack:
            return MonthStatService(**init_attributes)
        elif "year" in haystack:
            return YearStatService(**init_attributes)
        else:
            raise KeyError("No existing service for this.")