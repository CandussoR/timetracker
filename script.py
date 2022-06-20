import datetime
import clocks
from playsound import playsound
import re
import task_data
import timer_data
import timer_stats as stats

MENU_PROMPT = '''\n
Select an option:
    1) Start a timer,
    2) Take a break,
    3) Start a stopwatch,
    4) See some stats,
    5) Quit.\n
    '''

def start():
    connexion = task_data.connect()
    task_data.create_tables(connexion)

    while (user_input := int(input(MENU_PROMPT))) != 5:

        if user_input == 1:
            id = task_input_to_id(connexion)
            t_minutes = int(input("How long ? > "))*60
            timer_data.insert_beginning(connexion, id, datetime.datetime.now(), datetime.datetime.now())
            clocks.timer(t_minutes)
            print("Good job!")
            timer_data.update_row_at_ending(connexion, datetime.datetime.now())
            end_ring()

        elif user_input == 2:
            pause = int(input("How long ? > "))*60
            clocks.timer(pause)
            print("Back at it!")
            end_ring()

        elif user_input == 3:
            id = task_input_to_id(connexion)
            input("Press key when ready.")
            timer_data.insert_beginning(connexion, id, datetime.datetime.now(), datetime.datetime.now())
            clocks.stopwatch()
            timer_data.update_row_at_ending(connexion, datetime.datetime.now())

        elif user_input == 4:
            # Count number of timers and total time for different spans (day, week, year),
            # gives an average time per day and a maximum.
            today_timer = stats.timer_count(connexion, 'today')
            time_today = stats.total_time(connexion, 'today')
            suffix = 's' if today_timer > 1 else ''
            print(f"Today : {today_timer} timer{suffix} ({time_today}).")

            time_per_task = stats.time_per_task_today(connexion)
            for task, time in time_per_task:
                task_streak = stats.current_and_max_streak(connexion, task)
                max = "(max streak!)" if task_streak[0][1] == task_streak[0][0] else f"(max : {task_streak[0][0]})"
                print(f"\t{task} : {time}")
                print(f"\t\tCurrent streak : {task_streak[0][1]} {max}")

            avg_day = stats.average_day(connexion)
            print(f"\nYour average day : {avg_day}")

            max_stat = stats.max_in_a_day(connexion)
            print(f"\nYour maximum : {max_stat[1]} ({max_stat[0]}).\n")

            week_timer = stats.timer_count(connexion, 'week')
            time_week = stats.total_time(connexion, 'week')
            print(f"This week : {week_timer} timer{suffix} ({time_week}).\n")

            time_year = stats.total_time(connexion, 'year')
            year_timer = stats.timer_count(connexion, 'year')
            print(f"This year : {year_timer} timer{suffix} ({time_year}).\n")

        else:
            print("Invalid input, try again.")


def task_input_to_id(connexion):
    input_task = task_data.task_string_input()
    if re.search(r'\W', input_task):
        input_task = task_data.parse_input(input_task)
    else:
        input_task = [input_task]
    try:
        task_data.check_existence(connexion, *input_task)
        print("The task exists. Getting it's id...")
    except:
        print("The task doesn't exist yet. Adding it...")
        task_data.insert_new_task(connexion, *input_task)
        print("Getting it's id...")
    id = task_data.fetch_id(connexion, *input_task)
    return id

def end_ring():
    playsound('Flow.mp3')


if __name__ == '__main__':
    start()
