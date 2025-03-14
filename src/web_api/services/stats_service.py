from sqlite3 import Connection
from typing import Literal, Optional
from flask import g
from src.shared.repositories.stats_repository import SqliteStatRepository
from src.shared.utils.custom_dict_converter import convert_to_custom_dict
from src.shared.utils.format_time import format_time
from datetime import datetime, timedelta
from werkzeug.datastructures import ImmutableMultiDict
import calendar
from src.shared.utils.datetime_to_string import datetime_to_string as dts

from src.web_api.services.time_record_service import TimeRecordService

class BaseStatService():
    def __init__(self, connexion : Connection | None = None, request : ImmutableMultiDict | dict | None = None):
        '''Request is None to get home_stats or generic stats for period related to this day, else not None.'''
        self.connexion = g._database if connexion == None else connexion
        self.repo = SqliteStatRepository(self.connexion)
        self.original_request = request if request else None
        self.request = convert_to_custom_dict(request) if request else None
        if self.request :
            self.period, self.dates = self.get_period_and_dates(self.request)


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


    def get_period_and_dates(self, request : dict) -> tuple[str, str|list[str]] :
        keys = request.keys()

        if "period" in keys and "date" in keys and request["date"]:
            return request["period"], self.generate_dates_for_period(request["period"], request["date"])
        elif "period" in keys:
            return request["period"], self.generate_dates_for_period(request["period"])

        if "day" in keys :
            return "day", request["day"]

        elif "week" in keys:
            return "week", request["week"]
        
        elif set(["weekStart", "weekEnd"]).issubset(keys):
            return "week", request["weekStart"]
        elif "month" in keys :
            return "month", request["month"]

        elif "year" in keys :
            return "year", request["year"]

        elif set(["rangeBeginning", "rangeEnding"]).issubset(keys) :
            return "custom", [request["rangeBeginning"], request["rangeEnding"]]

        elif "tag" in keys:
            (fd,ld) = self.repo.get_first_and_last_date_in_db()
            return "custom", [fd,ld]

        else :
            raise KeyError("Period is not valid")
        
    
    def generate_dates_for_period(self, period : str, date : Optional[str] = None) -> str:
        '''
            Returns a list of one date (for day) or two dates (for any range).
        '''
        
        now = datetime.now()
        match(period):
            case "day":
                return dts('day', now) if not date else date
            case "week":
                if date:
                    d = datetime.strptime(date, '%Y-%M-%d')
                    start_of_week = d - timedelta(days=d.weekday())
                else:
                    start_of_week = now - timedelta(days=now.weekday())
                return dts('day', start_of_week)
            case "month":
                return date if date else dts('month', datetime(now.year, now.month, 1))
            case "year":
                return str(now.year) if not date else date
            case _:
                raise ValueError("Wrong period")
    

    def get_task_time_ratio(self) -> list[dict]:
        '''
            There's a little quirk here : if a week already set is to be passed, the dict must be of type `{"weekStart" : dt, "weekEnd" : dt}`.
            Otherwise, we take a specified period and do our little thing, and week is transformed in said way.
        '''
        assert self.request and self.request["period"] and ("date" in self.request or self.dates)
        # Preparing dict : this is a mess
        cp_request = self.request
        cp_request[self.request["period"]] = self.request["date"] if "date" in self.request else self.dates
        del cp_request['period']
        if "date" in cp_request:
            del cp_request['date']

        res = self.repo.get_task_time_ratio(cp_request)
        if res == None:
            return []

        data = []
        for task, time, ratio in res:
            if time == None:
                continue
            # if time exceeds a day
            if time > 86400:
               data.append({"task" : task, "time": time, "formatted": format_time(time, 'day', split=True), "ratio" : ratio})
            else :
                data.append({"task" : task, "time": time, "formatted": format_time(time, 'hour', split=True), "ratio" : ratio})
        return data


    def create_apex_line_chart_object(self, times : list[tuple], fill : int = 0, fill_value = None):
        '''
            Format data object for apexcharts LineBar in front.
            Returns a dict `{"name" : "Total time", "data": [an, array, of, int]}`
        '''
        line = {"name" : "Total time", "data" : [time for _,time in times]}
        line["data"].extend([fill_value] * fill)
        return line


    def create_apex_stacked_column_chart(self, ratios : list, labels : list):
        '''
            Format data object for apexcharts StackedBar in front.
            The fill value should only be used if the labels refer to future dates to cover the dates not yet present in the database.
        '''
        # (num_week, task_name, time_per_task, time_per_week, ratio)
        # Makes a list of the set of tasks so we can get an index
        tasks = list({t for _,t,_,_,_ in ratios})
        # Creating an object with values prefilled for each day of the week
        stacked = [{"name" : t, "data" : [0] * len(labels)} for t in tasks]

        for date, task, _, _, ratio in ratios:
            stacked[tasks.index(task)]["data"][labels.index(date)] = ratio

        return stacked


class DayStatService(BaseStatService):
    def __init__(self, connexion : Optional[Connection], request: Optional[ImmutableMultiDict] = None):
        super().__init__(connexion, request)


    def get_home_stat(self, a_date: Optional[str] = None):
        time_span = "today" if not a_date else None
        params = {"day": a_date} if a_date else None
        return  {
            "count": self.repo.timer_count(time_span, params),
            "time" : format_time(self.repo.total_time(time_span, params) or 0, "hour", split=True),
            "mean" : format_time(self.repo.mean_time_per_period("day"), "hour", split=True)
            }


    def get_task_time_ratio(self):
        return super().get_task_time_ratio()


    def get_generic_stat(self, a_date : str) -> dict:
        if not a_date:
            a_date = datetime.today().strftime('%Y-%m-%d')
        ret = {}
        ret["resume"] = self.get_home_stat(a_date)
        ret["detail"] = self.get_task_time_ratio()
        return ret


class WeekStatService(BaseStatService):
    def __init__(self, connexion : Optional[Connection], request: Optional[ImmutableMultiDict] = None):
        super().__init__(connexion, request)


    def get_home_stat(self, a_date : Optional[str] = None):
        mean_week = self.repo.mean_time_per_period("week")
        formatted_mean_week = format_time(mean_week, "day", split=True) if mean_week > 86400 else format_time(mean_week, "hour", split=True)
        time_span = "week" if not a_date else None
        params = None if not a_date else {"week" : a_date}
        return {
                    "count": self.repo.timer_count(time_span, params),
                    "time" : format_time(self.repo.total_time(time_span, params) or 0, "hour", split=True),
                    "mean": formatted_mean_week
                }


    def get_task_time_ratio(self):
        '''
            Get task_time_ratio according to the request passed : either with period, or with pair weekStart and weekEnd.
        '''
        return super().get_task_time_ratio()


    def get_generic_stat(self, week_beginning_date : str | None = None) :
        ret = {}
        if week_beginning_date:
            ret["resume"] = self.get_home_stat(week_beginning_date)

        # 1.1 Get all the dates for the current week
        # assuming Monday is the start of the week
        beginning_date : datetime|str = week_beginning_date or datetime.today()
        if isinstance(beginning_date, str):
            beginning_date = datetime.strptime(beginning_date, '%Y-%m-%d')

        start_of_week, end_of_week = self._get_week_range(beginning_date)

        days_in_week = self.get_column_dates(start_of_week)
        time_per_day = self.repo.total_time_per_day_in_range({"rangeBeginning" : days_in_week[0], "rangeEnding" : days_in_week[-1]})
        len_fill = 7 - len(time_per_day)

        # 1.2. Get task_time_ratio for every day of the week.
        ratios = self.repo.get_task_time_per_day_between(days_in_week[0], days_in_week[-1])
        stacked = super().create_apex_stacked_column_chart(ratios, days_in_week)

        # 2. Total time per day of the week
        days_line_chart = super().create_apex_line_chart_object(time_per_day, len_fill)

        ret["details"] = {"dates" : days_in_week, "stackedBarChart" : stacked, "daysLineChart": days_line_chart}
        return ret


    def get_column_dates(self, date : datetime | None = None):
        assert date is not None
        start_of_week = date - timedelta(days=date.weekday())
        return [*map(lambda x : x.strftime('%Y-%m-%d'), [start_of_week + timedelta(days=i) for i in range(7)])]


    def _get_week_range(self, a_date : Optional[datetime] = None):
        '''
            Return the first and last day of the week.
        '''
        today = datetime.now() if not a_date else a_date
        weekday = today.weekday()
        return [(today - timedelta(days=weekday)), (today + timedelta(days=6 - weekday))]


class MonthStatService(BaseStatService):
    def __init__(self, connexion : Optional[Connection], request: Optional[ImmutableMultiDict] = None):
        super().__init__(connexion, request)


    def get_home_stat(self, a_date : Optional[str] = None):
        mean_month = self.repo.mean_time_per_period("month")
        formatted_mean_month = format_time(mean_month, "day", split=True) if mean_month > 86400 else format_time(mean_month, "hour", split=True)
        time_span = "month" if not a_date else None
        params = None if not a_date else {"month" : a_date}
        return {
                    "count": self.repo.timer_count(time_span, params),
                    "time" : format_time(self.repo.total_time(time_span, params) or 0, "day", split=True),
                    "mean" : formatted_mean_month
                }


    def get_task_time_ratio(self):
        return super().get_task_time_ratio()


    def get_generic_stat(self, datestring : Optional[str] = None) -> dict:
        '''
            Gets a datetime object "YYYY-MM-DD" and returns a dict with :
            `weeks` : the week numbers of the month,
            `stackedBarChart` : data formated for Apex Charts Stacked Bar Chart,
            `weeksLineChart` : date formated for Apex Charts Line Chart.
        '''
        ret = {}
        if datestring:
            ret["resume"] = self.get_home_stat(datestring)

        # TODO : Must find a more robust solution
        original_datestring = datestring
        if not datestring :
            beginning_dt = datetime.now().replace(day=1)
            datestring = beginning_dt.strftime('%Y-%m-%d')
        elif len(datestring.split('-')) == 2:
            datestring = f"{datestring}-01"
        year,month,*_ = datestring.split('-')
        next_month = f"{year}-{int(month)+1:02d}-01"

        week_column_labels = self.get_column_dates(datestring)
        week_tasks_time = self.repo.get_task_time_ratio_by_week_between(datestring, next_month)

        label_and_time = []
        for i, *_ in week_tasks_time:
            label_and_time.append((week_column_labels[i], *_))

        # Graph stacked column chart
        stacked = super().create_apex_stacked_column_chart(label_and_time, week_column_labels)

        # Total time per week of the month
        if not original_datestring:
            week_times = self.repo.get_total_week_time_between(datestring, datetime.now().strftime('%Y-%m-%d'))
        else :
            week_times = self.repo.get_total_week_time_between(datestring, next_month)

        len_fill = len(week_column_labels) - len(week_times)

        week_line_chart = super().create_apex_line_chart_object(week_times, len_fill)

        ret["details"] = {"weeks" : week_column_labels, "stackedBarChart" : stacked, "weeksLineChart": week_line_chart }
        return ret


    def get_column_dates(self, datestring : str):
        a_date = datetime.strptime(datestring, '%Y-%m-%d')
        _,last_day = calendar.monthrange(a_date.year, a_date.month)
        _, first_week, _ = datetime(a_date.year, a_date.month, 1).isocalendar()
        _, last_week, _ = datetime(a_date.year, a_date.month, last_day).isocalendar()
        return [f'{week:02d}' for week in range(first_week, last_week+1)]
    

    def get_start_and_end_date_from_calendar_week(self, year, calendar_week):       
        monday = datetime.strptime(f'{year}-{calendar_week}-1', "%Y-%W-%w").date()
        return monday, monday + timedelta(days=6.9)


class YearStatService(BaseStatService):
    def __init__(self, connexion : Optional[Connection], request: Optional[ImmutableMultiDict] = None):
        super().__init__(connexion, request)


    def get_home_stat(self, a_date : Optional[str] = None):
        time_span = "year" if not a_date else None
        params = None if not a_date else {"year" : a_date}
        return {
                    "count": self.repo.timer_count(time_span, params),
                    "time" : format_time(self.repo.total_time(time_span, params) or 0, "day", split=True)
                }


    def get_task_time_ratio(self):
        return super().get_task_time_ratio()


    def get_generic_stat(self, year : Optional[str] = None) :
        ret = {}

        if year:
            ret["resume"] = self.get_home_stat(year)
        else:
            year = datetime.now().strftime('%Y')

        # 1.2. Get task_time_ratio for every month of year.
        ratios = self.repo.get_task_time_per_month_in_year(year)
        months = self.get_column_dates(year)
        time_per_month = self.repo.total_time_per_month_in_range(f'{year}-01-01', f'{year}-12-31')
        len_fill= 12 - len(time_per_month)

        stacked = super().create_apex_stacked_column_chart(ratios, months)

        # # 2. Total time per month of year
        line = super().create_apex_line_chart_object(time_per_month, len_fill)

        ret["details"] = {"months" : months,
                "stackedBarChart" : stacked,
                "monthsLineChart": line,
                "weekLineChart": self.get_total_time_per_week_for_year(year)}
        return ret


    def get_column_dates(self, year : str):
        return [f"{year}-{month:02d}" for month in range(1, 13)]


    def get_total_time_per_week_for_year(self, year : Optional[str] = None):
        '''
            Used to fill a year of week times in a bar chart in the front.
        '''
        try:
            res = self.repo.total_time_per_week_for_year(year)
            if res == [] : raise ValueError("No result")
            y_set = {year for (year, _, _) in res}
            obj = {}
            for y in y_set :
                # Too much coupling with apexcharts ?
                obj[y] = [{"x": week, "y": time} for (year, week, time) in res if year == y]
            return obj
        except Exception as e:
            raise Exception(e) from e


class CustomStatService():
    def __init__(self, connexion : Connection, request : dict):
        self.connexion = connexion
        self.request = request
        assert self.request != None
        self.logs = self.request["logs"] if "logs" in self.request else False


    def generate_labels(self, period, date_range : list[datetime]):
        if len(date_range) == 1 : return [date_range[0].strftime('%Y-%m-%d')]

        labels = []
        start_date, end_date = date_range

        if period == "day":
            labels = [*map(lambda x : x.strftime('%Y-%m-%d'), [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)])]

        elif period == "week":
            _, first_week, _ = start_date.isocalendar()
            _, last_week, _ = end_date.isocalendar()
            if first_week <= last_week:
                labels = [f'{week:02d}' for week in range(first_week, last_week+1)]
            else:
                labels = [f'{week:02d}' for week in range(first_week, 52+1)] + [f'{week:02d}' for week in range(1, last_week+1)]

        elif period == "month":
            if start_date.year == end_date.year:
                labels = [f"{start_date.year}-{month:02d}" for month in range(start_date.month, end_date.month+1)]
            else:
                labels.extend([f"{start_date.year}-{month:02d}" for month in range(start_date.month, 12+1)])
                labels.extend([f"{end_date.year}-{month:02d}" for month in range(1, end_date.month+1)])

        elif period == "year":
            labels = [str(start_date.year)] if start_date.year == end_date.year else [str(year) for year in range(start_date.year, end_date.year+1)]

        else:
            raise ValueError("Invalid period provided. Please choose from 'day', 'week', 'month', or 'year'.")

        return labels
    

    def get_generic_stats(self) -> dict:
        '''
        Returns generic stats for a period based on a date string.
        '''
        if "day" in self.request:
            return DayStatService(self.connexion, self.request).get_generic_stat(self.request["day"])
        if "week" in self.request:
            return WeekStatService(self.connexion, None).get_generic_stat(self.request["week"][0])
        if "month" in self.request:
            return MonthStatService(self.connexion, None).get_generic_stat(self.request["month"])
        if "year" in self.request:
            return YearStatService(self.connexion, self.request).get_generic_stat(str(self.request["year"]))
        else:
            return {}


    def get_custom_stats(self) -> dict:
        '''
            possible keys in the params dict :
                "day", "week", "year", "month", "rangeBeginning", "rangeEnding", "task", "subtask", "tag", "stats", "logs", "logSearch".
        '''
        assert self.request != None

        response_object = {}

        keys = self.request.keys()

        if len(keys) == 1 or (len(keys) == 2 and "logs" in keys):
            return self.get_generic_stats()
        
        if "rangeBeginning" in keys and not "stats" in keys :
            raise KeyError("Range must have a list of stat elements to return.")
        
        
        if "stats" in keys:
            response_object["stats"] = []
            for e in self.request["stats"]:
                if e["element"] == "timer-info":
                    t_i = {
                    "count": self.repo.timer_count(params=self.request),
                    "time" : format_time(self.repo.total_time(params=self.request), "day", split=True)
                    }
                    response_object["stats"].append({e["element"] : t_i})
                    continue

                if e["element"] == 'task-ratio':
                    response_object["stats"].append({e["element"] : super().get_task_time_ratio(self.dates)})
                    continue
                elif e["element"] == 'subtask-ratio':
                    response_object["stats"].append({e["element"] : self.repo.get_subtask_time_ratio(self.request)})
                    continue

                assert e.get("column-period") is not None, "This element always need a column period"
                assert len(self.dates) == 2
                
                labels = self.generate_labels(e["column-period"], self.dates)
                times = self._get_time_strategy(e["column-period"], self.dates)
                len_fill = len(labels) - len(times)
                if e["element"] == 'line-chart':
                    d = {
                        "labels": labels,
                        "series": super().create_apex_line_chart_object( times, len_fill, 0),
                        "title" : f"Total time for {e['column-period']}"
                    }
                    response_object["stats"].append({e["element"] : d})
                elif e["element"] == 'stacked-column-chart':
                    period = e["column-period"]
                    title = {"day" : "Task ratio per day", "week" : "Task ratio per week", "month" : "Task ratio per month", "year" : "Task ratio per day" }
                    ratios = self.repo.get_task_time(period, self.dates)
                    response_object["stats"].append({e["element"] : {"labels" : labels, "series" : super().create_apex_stacked_column_chart(ratios, labels), "title" : title[period]}})
                else :
                    raise KeyError("Wrong value for stat element.")

        if (set(["day", "weekStart", "month", "year"]).intersection(keys)
            and not "stats" in keys
            and not "tag" in keys
            and not "logs" in keys):
            response_object["stats"] = StatServiceFactory().create_stat_service(self.connexion, self.original_request).get_generic_stat(), 200

        if self.logs:
            time_record_service = TimeRecordService(connexion = self.connexion)
            response_object["logs"] = time_record_service.get_by(self.request)

        return response_object
    

    # def _get_time_strategy(self, for_period : str, dates : list[datetime]) -> list:
    #     #TODO : finish to refactor the different methods into one big.
    #     assert self.request

    #     match(for_period):
    #         case "day":
    #             return self.repo.total_time_per_day_in_range(self.request)
    #         case("week"):
    #             years = list(map(lambda x : str(x.year), dates))
    #             weeks = list(map(lambda x : f'{x.isocalendar()[1]:02d}', dates))
    #             return self.repo.total_time_per_week_in_range(years, weeks[0], weeks[1])
    #         case("month"):
    #             return self.repo.total_time_per_month_in_range(*dates)
    #         case("year"):
    #             return self.repo.total_time_per_year_in_range(dates)
    #         case _:
    #             raise ValueError("Wrong period for stats : ", for_period)


class StatServiceFactory():
    '''
        Factory that creates the service depending on a "period" key or a time span key (day, weekStart, month, year).
    '''
    @staticmethod
    def create_stat_service(connexion: Optional[Connection] = None, request: Optional[ImmutableMultiDict] = None):
        connexion = g._database if connexion is None else connexion
        if request is None: return BaseStatService(connexion)
        init_attributes = {"connexion" : connexion, "request": request}
        return StatServiceFactory.create_stat_object(request, init_attributes) 

    @staticmethod
    def create_stat_object(request_dict: dict, init_attributes: dict) -> BaseStatService|DayStatService|WeekStatService|MonthStatService|YearStatService:
        '''
            Takes in the converted request with the init_attributes for services, dict with connexion and request (unconverted) as keys.
        '''
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
