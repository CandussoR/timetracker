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
    connexion = db.connect(CONF.database)
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
                task_id = task_data.get_task_rank_from_input(connexion, task_input)
                tag_input = tag.ask_input()
                if tag_input:
                    tag_id = tag.retrieve_tag_id(connexion, tag_input)
                input("Press key when ready.")
            except KeyboardInterrupt:
                continue
            record = data.TimeRecord(task_id=task_id, date=datetime.datetime.now(), time_beginning=datetime.datetime.now(), tag_id=tag_id)
            record.id = data.insert_beginning(connexion, record)
            clocks.stopwatch()
            record.time_ending = datetime.datetime.now()
            print("Good job!")
            end_ring()
            record.log = enter_log()
            data.update_row_at_ending(connexion, record)

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
                record = data.TimeRecord()

                task_input = task_data.task_string_input()
                record.task_id = task_data.get_task_rank_from_input(connexion, task_input)
                tag_input = tag.ask_input()
                if tag_input:
                    record.tag_id = tag.retrieve_tag_id(connexion, tag_input)
                record.date = input("Date? (YYYY-MM-DD) > ")

                record.time_beginning = input("Beginning ? (HH:MM:SS) \n> ")

                record.time_ending = input("Ending ? (HH:MM:SS) \n> ")

                record.log = enter_log()
                data.insert_old_timer(connexion, record)

        elif user_input == 7:
            data.update_row_at_ending(connexion)
            print("Couldn't leave it huh ? Updated, boss.")

        elif user_input == 8:
            print("Not implemented. Logs, flows, etc. Probably only in GUI.")

        else:
            print("Invalid input, enter a number between 1 and 9.") 

def launch_timer(connexion : Connection, time_in_minutes : int | None = None):
    tag_id = None

    try:
        task_input = task_data.task_string_input()
        task_id = task_data.get_task_rank_from_input(connexion, task_input)
        tag_input = tag.ask_input()
        if tag_input:
            tag_id = tag.retrieve_tag_id(connexion, tag_input)
        if not time_in_minutes:
            time_in_minutes = int(input("How long ? > "))*60
        input("Press key when ready.")
    except KeyboardInterrupt: 
        raise KeyboardInterrupt
    
    record = data.TimeRecord(task_id=task_id, date=datetime.datetime.now(), time_beginning=datetime.datetime.now(), tag_id=tag_id)
    record.id = data.insert_beginning(connexion, record)
    clocks.timer(time_in_minutes)
    record.time_ending = datetime.datetime.now()
    print("Good job!")
    end_ring()
    record.log = enter_log()
    data.update_row_at_ending(connexion, record)

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
    log = None
    
    print("    Enter your log:")
    while True:
        piece = input("    > ")

        if piece == "":
            return log
        elif piece != "":
            log = piece
        else:
            log += f"  \n{piece}"        
        
if __name__ == '__main__':
    start()