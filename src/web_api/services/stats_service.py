from typing import Optional
from flask import g
from src.shared.repositories.stats_repository import SqliteStatRepository


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
                    obj[y] = [{"week": week, "time": time} for (year, week, _, _, time) in res if year == y]
                return obj
        except Exception as e:
            raise Exception(e) from e

            

