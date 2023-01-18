import datetime
import clocks
from playsound import playsound
import sqlite_db as db
import task_data
import timer_data as data
import timer_stats as stats

MENU_PROMPT = '''\n
Select an option :
    1) Start a timer,
    2) Take a break,
    3) Start a stopwatch,
    4) See some stats,
    5) Insert old timer,
    6) Extend last timer to now,
    7) Quit.\n

Use CTRL+C to come back here.
    '''

def start():
    connexion = db.connect('timer_data.db')
    db.create_tables(connexion)

    while (user_input := int(input(MENU_PROMPT))) != 7:

        if user_input == 1:
            try:
                id = task_data.task_input_to_id(connexion)
                t_minutes = int(input("How long ? > "))*60
                input("Press key when ready.")
            except KeyboardInterrupt: 
                continue
            data.insert_beginning(connexion, id, datetime.datetime.now(), datetime.datetime.now())
            clocks.timer(t_minutes)
            print("Good job!")
            data.update_row_at_ending(connexion, datetime.datetime.now())
            end_ring()

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
                id = task_data.task_input_to_id(connexion)
                input("Press key when ready.")
            except KeyboardInterrupt:
                continue
            data.insert_beginning(connexion, id, datetime.datetime.now(), datetime.datetime.now())
            clocks.stopwatch()
            data.update_row_at_ending(connexion, datetime.datetime.now())

        elif user_input == 4:
            stats.display_stats(connexion)
            
        elif user_input == 5:
            print("What task was it ?")
            id = task_data.task_input_to_id(connexion)

            print("Date? (YYYY-MM-DD) > ", end="")
            date = input()

            time_beginning = input("Beginning ? (HH:MM:SS) \n> ")

            time_ending = input("Ending ? (HH:MM:SS) \n> ")

            data.insert_old_timer(connexion, [id, date, time_beginning, time_ending])

        elif user_input == 6 :
             data.update_row_at_ending(connexion, datetime.datetime.now())
             print("Couldn't leave it huh ? Updated, boss.")

        else:
            print("Invalid input, enter a number between 1 and 7.") 

def end_ring():
    playsound('Flow.mp3')


if __name__ == '__main__':
    start()
