from datetime import datetime
from sqlite3 import Connection
from typing import Literal

from src.shared.repositories.stats_repository import SqliteStatRepository
from src.shared.utils.format_time import format_time

def display_stats(connexion : Connection):
    repo = SqliteStatRepository(connexion=connexion)
    # Count number of timers and total time for different spans (day, week, year),
    # gives an average time per day and a maximum.
    display_timer_count_and_time(repo, "today")
    
    for task, time, ratio in repo.get_task_time_ratio(range = [datetime.today()]):
        if time is not None:
            task_streak = repo.max_and_current_streaks(task)
            max = "(max streak!)" if task_streak[0][1] == task_streak[0][0] else f"(max : {task_streak[0][0]})"
            print(f"\t    {task} : {format_time(time, 'hour')} ({ratio}%)")
            print(f"\t\tCurrent streak : {task_streak[0][1]} {max}")

    print(f"\n\tThis year's average day : {repo.average_day_this_year() or 'No data yet.'}")

    max_stat = repo.max_in_a_day()
    print(f"\n\tYour maximum : {max_stat[1] or 'No data yet.'}{' ('+max_stat[0]+')' if max_stat[0] else ''}")

    display_timer_count_and_time(repo, "week")
    display_timer_count_and_time(repo, "year")
 
    more = input("\n\tSee every task max streak (y) ?\n  \t>> ")
    if more == 'y':
        for task, streak, current_streak in repo.all_task_streaks():
            suffix = f'(current : {current_streak})' if current_streak != 1 else ''
            print(f"  Max streak for {task} : {streak} {suffix}")


    weeks = input("\tSee last weeks (y) ?\n  \t>> ")
    if weeks == 'y':
        number_of_weeks : int = int(input("\tHow many ?\n\t>> "))
        time_per_week = repo.past_weeks(number_of_weeks)
        for monday, sunday, tpw in time_per_week:
            print(f"\tWeek from Monday {monday} to Sunday {sunday} : \n\t Total time : {tpw}")


def display_timer_count_and_time(repo : SqliteStatRepository, period : Literal["today", "week", "year"]) :
    match(period):
        case "today":
            range = "\tThis day"
        case "week":
            range = "\tThis week"
        case "year":
            range = "\tThis year"
        case _:
            raise Exception("Wrong argument.")    
            
    timer_count = repo.timer_count(period)
    suffix = 's' if timer_count > 1 else ''
    total_time = repo.total_time(period)
    newline = "\n" if period != "today" else ''
    if timer_count == 0:
        print(f"{newline}{range} : {timer_count} timer{suffix}.")
    elif total_time is None and timer_count == 1:
       print(f"{newline}{range} : {timer_count} timer{suffix} (ongoing).") 
    else:
        formatted = format_time(total_time, 'hour') if period != "year" else format_time(total_time, 'day')
        print(f"{newline}{range} : {timer_count} timer{suffix} ({formatted}).")
        
