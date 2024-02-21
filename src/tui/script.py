

# Prompt
from datetime import datetime
import os
from typing import Literal, Optional
from playsound import playsound
from src.shared.config.conf import Config
from src.shared.database import sqlite_db
from src.shared.flows import FlowCollection
from src.shared.models.tag import Tag
from src.shared.models.time_record import TimeRecordInput
from src.shared.repositories import stats_repository, tag_repository, task_repository, time_record_repository
import src.tui.clocks.clocks as clocks
from src.tui.input import tag_input, task_input
from src.tui.stats import stats_facade

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


def start(conf : Config, db_name : str):

    try:
        while (user_input := int(input(MENU_PROMPT))) != 9:

            if user_input == 1:
                try:
                    time_record = set_record(db_name)
                    launch_clock_facade(db_name, time_record, "timer")
                except KeyboardInterrupt:
                    continue
                print("Good job!")
                end_of_clock_facade(db_name, conf, time_record)

            elif user_input == 2:
                try :
                    launch_pause(None, conf)
                except KeyboardInterrupt:
                    continue

            elif user_input == 3:
                try:
                    time_record = set_record(db_name)
                    launch_clock_facade(db_name, time_record, "stopwatch")
                except KeyboardInterrupt:
                    continue
                print("Good job!")
                time_record.time_ending = datetime.now()
                time_record.log = enter_log()
                update_record(db_name, time_record)

            elif user_input == 4:
                try:
                    collection = FlowCollection(conf)
                    for i, flow in enumerate(collection.flows):
                        sets = [str(set) for set in flow.get_sets()]
                        print(f"    {i+1}) {flow.name} ;")
                        print(f"\t{len(sets)} sets : {', '.join(sets)}")
                    flow_number = int(input("    Which flow do you want to launch ?\r\n    > "))

                    for i, set in enumerate(collection.flows[flow_number - 1].get_sets()):
                        number_of_sets = len(sets)
                        print(f"    SET N°{i+1}/{number_of_sets}")
                        time_record = set_record(db_name)
                        launch_clock_facade(db_name, time_record, "timer", set[0] * 60)
                        end_of_clock_facade(db_name, conf, time_record)
                        launch_pause(set[1] * 60, conf)
                except KeyboardInterrupt :
                    continue

            elif user_input == 5:
                try:
                    connexion = sqlite_db.connect(db_name)
                    stats_facade.display_stats(connexion)
                    connexion.close()
                except KeyboardInterrupt:
                    continue
                
            elif user_input == 6:
                time_record = set_record(db_name, old = True)
                connexion = sqlite_db.connect(db_name)
                time_record_repo = time_record_repository.SqliteTimeRecordRepository(connexion = connexion)
                time_record_repo.insert_old_timer(time_record)
                connexion.commit()
                connexion.close()

            elif user_input == 7:
                connexion = sqlite_db.connect(db_name)
                time_record_repo = time_record_repository.SqliteTimeRecordRepository(connexion = connexion)
                time_record_repo.update_last_row_ending(datetime.now())
                connexion.commit()
                connexion.close()
                print("Couldn't leave it huh ? Updated, boss.")

            elif user_input == 8:
                print("Not implemented. Logs, flows, etc. Probably only in GUI.")

            else:
                print("Invalid input, enter a number between 1 and 9.")

    except (ValueError, KeyboardInterrupt):
        print("See ya!\n")


def launch_clock_facade(db_name : str, time_record : TimeRecordInput, clock : Literal["timer", "stopwatch"], duration : int | None = None) :
    if duration:
        time_in_minutes = duration
    elif (not duration) and clock == "timer":
        time_in_minutes = int(input("How long ? > "))*60

    input("Press key when ready.")

    time_record.time_beginning = datetime.now()
    insert_record(db_name, time_record)

    if clock == "timer":
        start_clock("timer", time_in_minutes)
    else :
        start_clock("stopwatch")


def end_of_clock_facade(db_name : str, conf : Config, time_record : TimeRecordInput):
    time_record.time_ending = datetime.now()
    end_ring(conf)
    time_record.log = enter_log()
    update_record(db_name, time_record)


def set_record(db_name : str, old : bool = False) :
    '''Takes the input for the TimeRecord.'''
    connexion = sqlite_db.connect(db_name)
    tag_repo = tag_repository.SqliteTagRepository(connexion=connexion)
    task_repo = task_repository.SqliteTaskRepository(connexion=connexion)
    tag_id = None
    task = task_input.task_string_input()
    task_id = task_input.get_task_rank_from_input(task_repo, task)
    tag = tag_input.ask_input()
    if tag:
        tag_id = tag_input.get_tag_id_from_input(tag_repo, tag)
    time_record = TimeRecordInput(task_id=task_id, date=datetime.now(), tag_id=tag_id)
    if old:
        time_record.date = input("Date? (YYYY-MM-DD) > ")
        time_record.time_beginning = input("Beginning ? (HH:MM:SS) \n> ")
        time_record.time_ending = input("Ending ? (HH:MM:SS) \n> ")
        time_record.log = enter_log()
    return time_record


def insert_record(db_name : str, time_record : TimeRecordInput) :
    '''Insert time record and adds its guid.'''
    with sqlite_db.connect(db_name) as connexion :
        repo = time_record_repository.SqliteTimeRecordRepository(connexion = connexion)
        repo.insert_beginning(time_record)
        connexion.commit()
        

def update_record(db_name : str, time_record : TimeRecordInput):
    with sqlite_db.connect(db_name) as connexion:
        repo = time_record_repository.SqliteTimeRecordRepository(connexion = connexion)
        time_record.guid = repo.update_row_at_ending(time_record)
        connexion.commit() 


def start_clock(clock : Literal["timer", "stopwatch"], times_in_minutes : Optional[int] = None) :
    if clock == "timer":
        clocks.timer(times_in_minutes)
    if clock == "stopwatch":
        clocks.stopwatch()


def launch_pause(time_in_minutes : int | None, conf: Config):
    try:
        if not time_in_minutes :
            time_in_minutes = int(input("How long ? > "))*60
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    start_clock("timer", time_in_minutes)
    print("Back at it!")
    end_ring(conf)


def end_ring(conf : Config):
    playsound(conf.timer_sound_path)


def enter_log() -> str:
    log = None
    
    print("Enter your log :")
    while True:
        piece = input("    > ")

        if piece == "":
            return log
        elif piece != "" and not log:
            log = piece
        else:
            log += f"  \n{piece}"        
        
if __name__ == '__main__':
    start()
