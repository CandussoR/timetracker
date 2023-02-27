import datetime
import clocks
from playsound import playsound
import sqlite_db as db
import task_data
import timer_data as data
import timer_stats as stats
import parse_conf as pc
import task_logs as tl

# Conf
CONF = pc.load_conf("conf.json")
LOGS = CONF['log']

# Prompt
prompt_seven = "Deactivate logs," if LOGS else "Activate logs,"
MENU_PROMPT = f'''\n
Select an option :
    1) Start a timer,
    2) Take a break,
    3) Start a stopwatch,
    4) See some stats,
    5) Insert old timer,
    6) Extend last timer to now,
    7) {prompt_seven},
    8) Quit.\n
    '''


def start():
    connexion = db.connect('timer_data.db')
    db.create_tables(connexion)

    while (user_input := int(input(MENU_PROMPT))) != 8:

        if user_input == 1:
            try:
                task_input = task_data.task_string_input()
                (id, task, subtask) = task_data.get_task_rank_from_input(connexion, task_input)
                t_minutes = int(input("How long ? > "))*60
                input("Press key when ready.")
            except KeyboardInterrupt: 
                continue
            data.insert_beginning(connexion, id, datetime.datetime.now(), datetime.datetime.now())
            clocks.timer(t_minutes)
            print("Good job!")
            data.update_row_at_ending(connexion, datetime.datetime.now())
            end_ring()
            if LOGS:
                tl.write_log(CONF["log_path"], task, subtask)
                print("Logs functionality will come.")

        elif user_input == 2:
            try:
                pause = int(input("How long ? > "))*60
            except KeyboardInterrupt:
                continue
            clocks.timer(pause)
            print("Back at it!")
            end_ring()

        elif user_input == 3:
            try:
                task_input = task_data.task_string_input()
                (id, task, subtask) = task_data.get_task_rank_from_input(connexion, task_input)
                input("Press key when ready.")
            except KeyboardInterrupt:
                continue
            data.insert_beginning(connexion, id, datetime.datetime.now(), datetime.datetime.now())
            clocks.stopwatch()
            data.update_row_at_ending(connexion, datetime.datetime.now())
            end_ring()
            if LOGS:
                tl.write_log(CONF["log_path"], task, subtask)

        elif user_input == 4:
            try:
                stats.display_stats(connexion)
            except KeyboardInterrupt:
                continue
            
        elif user_input == 5:
            task_input = task_data.task_string_input()
            (id, task, subtask) = task_data.get_task_rank_from_input(connexion, task_input)

            print("Date? (YYYY-MM-DD) > ", end="")
            date = input()

            time_beginning = input("Beginning ? (HH:MM:SS) \n> ")

            time_ending = input("Ending ? (HH:MM:SS) \n> ")

            data.insert_old_timer(connexion, [id, date, time_beginning, time_ending])

        elif user_input == 6 :
            data.update_row_at_ending(connexion, datetime.datetime.now())
            print("Couldn't leave it huh ? Updated, boss.")

        elif user_input == 7:
            pc.switch_logs(CONF, "conf.json")

        else:
            print("Invalid input, enter a number between 1 and 7.") 

def end_ring():
    playsound('Flow.mp3')


if __name__ == '__main__':
    start()
