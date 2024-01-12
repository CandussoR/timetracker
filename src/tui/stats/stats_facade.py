from sqlite3 import Connection

from src.shared.repositories.stats_repository import SqliteStatRepository

def display_stats(connexion : Connection):
    repo = SqliteStatRepository(connexion=connexion)
    # Count number of timers and total time for different spans (day, week, year),
    # gives an average time per day and a maximum.
    today_timer = repo.timer_count('today')
    suffix = 's' if today_timer > 1 else ''
    print(f"Today : {today_timer} timer{suffix} ({repo.total_time('today')}).")

    for task, time in repo.time_per_task_today():
        task_streak = repo.max_and_current_streaks(task)
        max = "(max streak!)" if task_streak[0][1] == task_streak[0][0] else f"(max : {task_streak[0][0]})"
        print(f"\t{task} : {time}")
        print(f"\t\tCurrent streak : {task_streak[0][1]} {max}")

    print(f"\nThis year's average day : {repo.average_day_this_year()}")

    max_stat = repo.max_in_a_day()
    print(f"\nYour maximum : {max_stat[1]} ({max_stat[0]}).\n")

    print(f"This week : { repo.timer_count('week') } timer{suffix} ({ repo.total_time('week') }).\n")

    print(f"This year : {repo.timer_count('year')} timer{suffix} ({repo.total_time('year')}).\n")

    more = input("See every task max streak (y) ?\n\t>> ")
    if more == 'y':
        repo.all_task_streaks()

    weeks = input("See last weeks (y) ?\n\t>> ")
    if weeks == 'y':
        number_of_weeks : int = int(input("\tHow many ?\n\t>> "))
        repo.past_weeks(number_of_weeks)