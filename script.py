import datetime
import clocks
import task_data
import timer_data
import timer_stats as stats

MENU_PROMPT = '''\n
Sélectionnez une option:
    1) Lancer un timer,
    2) Faire une pause,
    3) Lancer un chrono,
    4) Voir les stats,
    5) Quitter.\n
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
            timer_data.updating_row(connexion, datetime.datetime.now())

        elif user_input == 2:
            pass
            # Pause de combien de temps ?
            pause = int(input("How long ? > "))*60
            # Lancer un timer.
            clocks.timer(pause)

        elif user_input == 3:
            id = task_input_to_id(connexion)
            timer_data.insert_beginning(connexion, id, datetime.datetime.now(), datetime.datetime.now())
            clocks.stopwatch()
            timer_data.updating_row(connexion, datetime.datetime.now())

        elif user_input == 4:
            today_timer = stats.timer_count(connexion, 'today')
            week_timer = stats.timer_count(connexion, 'week')
            year_timer = stats.timer_count(connexion, 'year')
            time_today = stats.total_time(connexion, 'today')
            time_week = stats.total_time(connexion, 'week')
            time_year = stats.total_time(connexion, 'year')
            max_stat = stats.max_in_a_day(connexion)

            suffix = 's' if today_timer > 1 else ''
            print(f"\n\tToday : \n{today_timer} timer{suffix} ({time_today}).\n")
            print(f"Your maximum : {max_stat[1]} le {max_stat[0]}.\n")
            print(f"\tThis week : \n{week_timer} timer{suffix} ({time_week}).\n")
            print(f"\t This year : \n{year_timer} timer{suffix} ({time_year}).\n")

            print("\tWhat you've done today :")
            time_per_task = stats.time_per_task_today(connexion)
            for task, time in time_per_task:
                print(f"{task} for {time}")

        else:
            print("Invalid input, try again.")

def task_input_to_id(connexion):
    input_task = input("What do we do ? > ")
    try:
        task_data.check_existence(connexion, input_task)
        print("The task exists. Getting it's id...")
    except:
        print("The task doesn't exist yet. Adding it...")
        task_data.insert_new_task(connexion, input_task)
        print("Getting it's id...")
    id = task_data.fetch_id(connexion, input_task)
    return id

start()
