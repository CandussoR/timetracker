from typing import Optional
from flask import g
from src.shared.repositories.stats_repository import SqliteStatRepository
from src.shared.utils.format_time import format_time
from datetime import datetime, timedelta
import traceback



class StatService():
    def __init__(self):
        self.connexion = g._database
        self.repo = SqliteStatRepository(self.connexion)

    def get_home_stats(self):
        try: 
            home = {
                "daily" : {
                    "count": self.repo.timer_count("today"),
                    "time" : self.repo.total_time("today")
                }, 
                "weekly" : {
                    "count": self.repo.timer_count("week"),
                    "time" : self.repo.total_time("week")
                },
                "monthly" : {
                    "count": self.repo.timer_count("month"),
                    "time" : self.repo.total_time("month")
                },
                "yearly" : {
                    "count": self.repo.timer_count("year"),
                    "time" : self.repo.total_time("year")
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
        try:
            # 1.2. Get task_time_ratio for every day of the week.
            month = datetime.today().strftime('%Y-%m')
            ratios = []
            ratios.extend(self.repo.get_task_time_per_week_in_month(month))

            weeks = {w for w,_,_,_,_ in ratios}
            tasks = {t for _,t,_,_,_ in ratios}

            stacked = []
            for w in weeks:
                stacked.append({"name" : w, "data" : [0] * len(tasks)})
            for week,task,_,_,ratio in ratios:
                i_week = [i for i, w in enumerate(weeks) if w == week][0]
                i_task = [i for i, t in enumerate(tasks) if t == task][0]
                stacked[i_week]["data"][i_task] = ratio
            print("stacked", stacked)
            # for d in days_in_week:
            #     ratios.append(self.repo.get_task_time_ratio({"period": "day", "date": d}))

            # # Too much coupling with apexcharts ?
            # # 1.3. Format data object for apexcharts loading StackedBar with VueJs 
            # unique_tasks = {task for r in ratios for _, task, _, _ in r}
            # # 1.3.2. Creating an object with values prefilled for each day
            # stacked = []
            # for t in unique_tasks:
            #     stacked.append({"name" : t, "data" : [0] * 7})
            # stacked_tasks = [obj["name"] for obj in stacked]

            # for sublist in ratios:
            #     for item in sublist:
            #         index = stacked_tasks.index(item[1])
            #         stacked[index]["data"][ratios.index(sublist)] = item[3]

            # # 2. Total time per day of the week
            # days_line_chart = self.repo.total_time_per_day_in_range(days_in_week[0], days_in_week[-1])
            # days_line_chart = {"name" : "Total time", "data" : [time for _,time in days_line_chart]}
            # len_fill = 7 - len(days_line_chart["data"])
            # if len_fill:
            #     days_line_chart["data"].extend([None] * len_fill)

            # return {"dates" : days_in_week, "stackedBarChart" : stacked, "daysLineChart": days_line_chart}     
            return {"month": stacked}   
        except Exception as e:
            print(e)
            tb = traceback.format_exc()
            print(tb)
            raise Exception(e) from e
