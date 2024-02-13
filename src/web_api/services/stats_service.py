from typing import Optional
from flask import g
from src.shared.repositories.stats_repository import SqliteStatRepository
from src.shared.utils.format_time import format_time


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
            


            

