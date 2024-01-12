

def display_stats(connexion : Connection):
    # Count number of timers and total time for different spans (day, week, year),
    # gives an average time per day and a maximum.
    today_timer = timer_count(connexion, 'today')
    suffix = 's' if today_timer > 1 else ''
    print(f"Today : {today_timer} timer{suffix} ({total_time(connexion, 'today')}).")

    for task, time in time_per_task_today(connexion):
        task_streak = max_and_current_streaks(connexion, task)
        max = "(max streak!)" if task_streak[0][1] == task_streak[0][0] else f"(max : {task_streak[0][0]})"
        print(f"\t{task} : {time}")
        print(f"\t\tCurrent streak : {task_streak[0][1]} {max}")

    print(f"\nThis year's average day : {average_day_this_year(connexion)}")

    max_stat = max_in_a_day(connexion)
    print(f"\nYour maximum : {max_stat[1]} ({max_stat[0]}).\n")

    print(f"This week : { timer_count(connexion, 'week') } timer{suffix} ({ total_time(connexion, 'week') }).\n")

    print(f"This year : {timer_count(connexion, 'year')} timer{suffix} ({total_time(connexion, 'year')}).\n")

    more = input("See every task max streak (y) ?\n\t>> ")
    if more == 'y':
        all_task_streaks(connexion)

    weeks = input("See last weeks (y) ?\n\t>> ")
    if weeks == 'y':
        number_of_weeks : int = int(input("\tHow many ?\n\t>> "))
        past_weeks(connexion, number_of_weeks)