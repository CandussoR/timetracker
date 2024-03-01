from typing import Optional
from flask import g
from src.shared.repositories.stats_repository import SqliteStatRepository
from src.shared.utils.format_time import format_time
from datetime import datetime, timedelta
import calendar



class StatService():
    def __init__(self):
        self.connexion = g._database
        self.repo = SqliteStatRepository(self.connexion)

    def get_home_stats(self):
        try: 
            home = {
                "daily" : {
                    "count": self.repo.timer_count("today"),
                    "time" : format_time(self.repo.total_time("today") or 0, "hour")
                }, 
                "weekly" : {
                    "count": self.repo.timer_count("week"),
                    "time" : format_time(self.repo.total_time("week") or 0, "hour")
                },
                "monthly" : {
                    "count": self.repo.timer_count("month"),
                    "time" : format_time(self.repo.total_time("month"), "day")
                },
                "yearly" : {
                    "count": self.repo.timer_count("year"),
                    "time" : format_time(self.repo.total_time("year"), "day")
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
           Returns the total time and ratio for a task during a certain period.
           params can be `{"period" : year|month|week|day, "task" : a task, "tag" : a tag}`
           or at least one param.
        '''
        res = self.repo.get_task_time_ratio(params)
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
    
    def get_generic_week(self):
        # 1.1 Get all the dates for the current week
        # assuming Monday is the start of the week
        today = datetime.today()
        start_of_week = today - timedelta(days=today.weekday())
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
    
    def get_generic_month(self):
        # 1.2. Get task_time_ratio for every day of the week.
        now = datetime.now()
        month = now.strftime('%Y-%m')
        number_of_weeks = len(calendar.monthcalendar(now.year, now.month))

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

        # # 2. Total time per day of the week
        weeks = list(weeks)
        weeks_line_chart = self.repo.total_time_per_week_in_range(weeks[0], weeks[-1])
        weeks_line_chart = {"name" : "Total time", "data" : [time for _,time in weeks_line_chart]}
        len_fill = number_of_weeks - len(weeks_line_chart["data"])
        if len_fill:
            weeks_line_chart["data"].extend([None] * len_fill)

        return {"weeks" : weeks, "stackedBarChart" : stacked, "weeksLineChart": weeks_line_chart}       

    def get_generic_year(self):
        # 1.2. Get task_time_ratio for every day of the week.
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
        print(months_line_chart)
        months_line_chart = {"name" : "Total time", "data" : [time for _,time in months_line_chart]}
        len_fill = 12 - len(months_line_chart["data"])
        if len_fill:
            months_line_chart["data"].extend([None] * len_fill)

        return {"months" : months, 
                "stackedBarChart" : stacked, 
                "monthsLineChart": months_line_chart, 
                "weekLineChart": self.get_week_total_time({"years[]" : year})}