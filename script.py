import datetime
from sqlite3 import Connection
import clocks
from playsound import playsound
from flows import FlowCollection, Flow
import sqlite_db as db
import task_data
import timer_data as data
import timer_stats as stats
from conf import Config
import task_logs as tl
import tag

# Conf
# CONF = c.load_conf("conf.json")
CONF = Config()
LOGS = CONF.logs

# Prompt
MENU_PROMPT = f'''\n
Select an option :
    1) Start a timer,
    2) Take a break,
    3) Start a stopwatch,
    4) Launch a Flow
    5) See some stats,
    6) Insert old timer,
    7) Extend last timer to now,
    8) Settings,
    9) Quit.\n
    '''


def start():
    # connexion = db.connect(CONF.database)
    connexion = db.connect("db_test.db")
    db.create_tables(connexion)

    while (user_input := int(input(MENU_PROMPT))) != 8:

        if user_input == 1:
            try:
                launch_timer(connexion)
            except KeyboardInterrupt:
                continue

        elif user_input == 2:
            try :
                launch_pause()
            except KeyboardInterrupt:
                continue

        elif user_input == 3:
            tag_id = None
            try:
                task_input = task_data.task_string_input()
                (id, task, subtask) = task_data.get_task_rank_from_input(connexion, task_input)
                tag_input = tag.ask_input()
                if tag_input:
                    tag_id = tag.retrieve_tag_id(connexion, tag_input)
                input("Press key when ready.")
            except KeyboardInterrupt:
                continue
            last_id = data.insert_beginning(connexion, id, datetime.datetime.now(), datetime.datetime.now(), tag_id)
            clocks.stopwatch()
            end_time = datetime.datetime.now()
            end_ring()
            log = enter_log()
            data.update_row_at_ending(connexion, last_id, end_time, log)
            # if LOGS:
            #     tl.write_log(CONF.log_path, task, subtask)

        elif user_input == 4:
            try:
                collection = FlowCollection(CONF)
                for i, flow in enumerate(collection.flows):
                    sets = flow.get_sets()
                    sets = [str(set) for set in sets]
                    print(f"    {i+1}) {flow.name} ;")
                    print(f"\t{len(sets)} sets : {', '.join(sets)}")
                flow_number = int(input("    Which flow do you want to launch ?\r\n    > "))

                for i, set in enumerate(collection.flows[flow_number - 1].get_sets()):
                    number_of_sets = len(sets)
                    print(f"    SET N°{i+1}/{number_of_sets}")
                    launch_timer(connexion, set[0])
                    launch_pause(set[1])
            except KeyboardInterrupt as e:
                continue

        elif user_input == 5:
            try:
                stats.display_stats(connexion)
            except KeyboardInterrupt:
                continue
            
        elif user_input == 6:
                tag_id = None

                task_input = task_data.task_string_input()
                (id, task, subtask) = task_data.get_task_rank_from_input(connexion, task_input)
                tag_input = tag.ask_input()
                if tag_input:
                    tag_id = tag.retrieve_tag_id(connexion, tag_input)
                date = input("Date? (YYYY-MM-DD) > ")

                time_beginning = input("Beginning ? (HH:MM:SS) \n> ")

                time_ending = input("Ending ? (HH:MM:SS) \n> ")

                log = enter_log()
                data.insert_old_timer(connexion, id, date, time_beginning, time_ending, tag_id, log)

        elif user_input == 7:
            data.update_row_at_ending(connexion, datetime.datetime.now())
            print("Couldn't leave it huh ? Updated, boss.")

        elif user_input == 8:
            print("Not implemented. Logs, flows, etc. Probably only in GUI.")

        else:
            print("Invalid input, enter a number between 1 and 9.") 

def launch_timer(connexion : Connection, time_in_minutes : int | None = None):
    tag_id = None

    try:
        task_input = task_data.task_string_input()
        (id, task, subtask) = task_data.get_task_rank_from_input(connexion, task_input)
        tag_input = tag.ask_input()
        if tag_input:
            tag_id = tag.retrieve_tag_id(connexion, tag_input)
        if not time_in_minutes:
            time_in_minutes = int(input("How long ? > "))*60
        input("Press key when ready.")
    except KeyboardInterrupt: 
        raise KeyboardInterrupt
    
    row_id = data.insert_beginning(connexion, id, datetime.datetime.now(), datetime.datetime.now(), tag_id)
    clocks.timer(time_in_minutes)
    end_time = datetime.datetime.now()
    print("Good job!")
    end_ring()
    log = enter_log()
    data.update_row_at_ending(connexion, row_id, end_time, log)
    # if LOGS:
    #     tl.write_log(CONF.log_path, task, subtask)

def launch_pause(time_in_minutes : int | None):
    try:
        if not time_in_minutes :
            time_in_minutes = int(input("How long ? > "))*60
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    clocks.timer(time_in_minutes)
    print("Back at it!")
    end_ring()

def end_ring():
    playsound(CONF.timer_sound_path)

def enter_log() -> str:
    log = ""
    
    print("    Enter your log:")
    while True:
        piece = input("    > ")

        if piece == "":
            return log
        if piece != "" and log == "":
            log += piece
        else:
            log += f"  \n{piece}"        
        

if __name__ == '__main__':
    start()