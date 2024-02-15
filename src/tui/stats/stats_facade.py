from sqlite3 import Connection

from src.shared.repositories.stats_repository import SqliteStatRepository
from src.shared.utils.format_time import format_time

def display_stats(connexion : Connection):
    repo = SqliteStatRepository(connexion=connexion)
    # Count number of timers and total time for different spans (day, week, year),
    # gives an average time per day and a maximum.
    # today_timer = repo.timer_count('today')
    # suffix = 's' if today_timer > 1 else ''
    # print(f"Today : {today_timer} timer{suffix} ({repo.total_time('today')}).")
    
    # for _, task, time, ratio in repo.get_task_time_ratio({"period": "day"}):
    #     task_streak = repo.max_and_current_streaks(task)
    #     max = "(max streak!)" if task_streak[0][1] == task_streak[0][0] else f"(max : {task_streak[0][0]})"
    #     print(f"\t{task} : {format_time(time, 'hour')} ({ratio}%)")
    #     print(f"\t\tCurrent streak : {task_streak[0][1]} {max}")

    # print(f"\nThis year's average day : {repo.average_day_this_year()}")

    # max_stat = repo.max_in_a_day()
    # print(f"\nYour maximum : {max_stat[1]} ({max_stat[0]}).\n")

    # print(f"This week : { repo.timer_count('week') } timer{suffix} ({ repo.total_time('week') }).\n")

    # print(f"This year : {repo.timer_count('year')} timer{suffix} ({repo.total_time('year')}).\n")

    more = input("See every task max streak (y) ?\n\t>> ")
    if more == 'y':
        for task, streak, current_streak in repo.all_task_streaks():
            suffix = f'(current : {current_streak})' if current_streak != 1 else ''
            print(f"  Max streak for {task} : {streak} {suffix}")


    weeks = input("See last weeks (y) ?\n\t>> ")
    if weeks == 'y':
        number_of_weeks : int = int(input("\tHow many ?\n\t>> "))
        time_per_week = repo.past_weeks(number_of_weeks)
        for monday, sunday, tpw in time_per_week:
            print(f"Week from Monday {monday} to Sunday {sunday} : \n\t Total time : {tpw}")
