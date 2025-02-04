# Prompt
from datetime import datetime, date
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


def start(conf : Config, db_name : str):

    menu_prompt = f'''\n
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
    > '''

    # We show the prompt only at entry or after each action effectively done.
    show_prompt = True
    
    try:
        while (user_input := input(menu_prompt if show_prompt else '\n    > ')) != "9":

            show_prompt = False

            user_input = user_input.strip()

            if len(user_input) == 0:
                print("\tHit Ctrl+C or 9 if you want to quit.")
                continue
            
            match(user_input):
                case "1":
                    try:
                        time_record = set_record(db_name)
                        launch_clock_facade(db_name, time_record, "timer")
                    except KeyboardInterrupt:
                        continue
                    print("\tGood job!")
                    end_of_clock_facade(db_name, conf, time_record)
                    show_prompt = True
                
                case "2":
                    try :
                        launch_pause(None, conf)
                    except KeyboardInterrupt:
                        continue
                    show_prompt = True


                case "3":
                    try:
                        time_record = set_record(db_name)
                        launch_clock_facade(db_name, time_record, "stopwatch")
                    except KeyboardInterrupt:
                        continue
                    print("\tGood job!")
                    time_record.time_ending = datetime.now()
                    time_record.log = enter_log()
                    update_record(db_name, time_record)
                    show_prompt = True


                case "4":
                    try:
                        collection = FlowCollection(conf)
                        for i, flow in enumerate(collection.flows):
                            sets = [str(set) for set in flow.get_sets()]
                            print(f"    {i+1}) {flow.name} ;")
                            print(f"\t{len(sets)} sets : {', '.join(sets)}")
                        flow_number = int(input("    Which flow do you want to launch ?\r\n    > "))
                        show_prompt = True

                        for i, set in enumerate(collection.flows[flow_number - 1].get_sets()):
                            number_of_sets = len(sets)
                            print(f"    SET N°{i+1}/{number_of_sets}")
                            time_record = set_record(db_name)
                            launch_clock_facade(db_name, time_record, "timer", set[0] * 60)
                            end_of_clock_facade(db_name, conf, time_record)
                            launch_pause(set[1] * 60, conf)
                    except KeyboardInterrupt :
                        continue

                case "5":
                    try:
                        connexion = sqlite_db.connect(db_name)
                        stats_facade.display_stats(connexion)
                        connexion.close()
                        show_prompt = True
                    except KeyboardInterrupt:
                        continue

                case "6":
                    try:
                        time_record = set_record(db_name, old = True)
                        connexion = sqlite_db.connect(db_name)
                        time_record_repo = time_record_repository.SqliteTimeRecordRepository(connexion = connexion)
                        time_record_repo.insert_old_timer(time_record)
                        connexion.commit()
                        connexion.close()
                        show_prompt = True
                    except KeyboardInterrupt:
                        continue

                case "7":
                    connexion = sqlite_db.connect(db_name)
                    time_record_repo = time_record_repository.SqliteTimeRecordRepository(connexion = connexion)
                    time_record_repo.update_last_row_ending(datetime.now())
                    connexion.commit()
                    connexion.close()
                    print("\tCouldn't leave it huh ? Updated, boss.")

                case "8":
                    print("\tNot implemented.")
                    print("\fIf you want to create a flow, you have to add it manually to your config file.")

                case "9":
                    print("\tBye !")

                case _:
                    print("\tInvalid input, enter a number between 1 and 9.")
        
    except (KeyboardInterrupt):
        print("\tBye!\n")


def launch_clock_facade(
    db_name: str,
    time_record: TimeRecordInput,
    clock: Literal["timer", "stopwatch"],
    duration: int | None = None,
):
    if duration:
        time_in_minutes = duration
    elif (not duration) and clock == "timer":
        time_in_minutes = int(input("\tHow long ? > ")) * 60

    input("\tPress key when ready.")

    time_record.time_beginning = datetime.now()
    insert_record(db_name, time_record)

    if clock == "timer":
        start_clock("timer", time_record.time_beginning, time_in_minutes)
    else :
        start_clock("stopwatch", time_record.time_beginning)


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
        time_record.date = ask_date_input()
        time_record.time_beginning = ask_time_input("beginning", time_record.date)
        time_record.time_ending = ask_time_input("ending", time_record.date)
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


def start_clock(
    clock: Literal["timer", "stopwatch"],
    time_beginning: Optional[datetime] = None,
    times_in_minutes: Optional[int] = None,
):
    if clock == "timer" and time_beginning:
        clocks.timer(time_beginning, times_in_minutes)
    elif clock == "stopwatch":
        clocks.stopwatch(time_beginning)


def launch_pause(time_in_minutes: int | None, conf: Config):
    try:
        if not time_in_minutes :
            time_in_minutes = int(input("\tHow long ? > "))*60
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    start_clock("timer", time_beginning=datetime.now(), times_in_minutes=time_in_minutes)
    print("\tBack at it!")
    end_ring(conf)


def end_ring(conf : Config):
    playsound(conf.timer_sound_path)


def enter_log() -> str | None:
    log = None
    
    print("\tEnter your log :")
    while True:
        piece = input("\t    > ")

        if not piece:
            return log
        if piece and not log:
            log = piece
        elif piece and log:
            log += f"  \n{piece}" 

def ask_date_input() -> str:
    while True:
        val =  input("\tDate? (YYYY-MM-DD) \n\t> ")
        try:
            val_date = date.fromisoformat(val)
            if val_date and val_date <= datetime.now().date():
                return val
            else:
                print("\t    Date is in the future, not you.")
        except ValueError:
            print("\t    Invalid date.")


def ask_time_input(bound : Literal["beginning", "ending"], date) -> str:
    while True:
        val = input(f"\t{bound.title()} time? (HH:MM:SS) \n\t> ")
        try:
            val_time = datetime.strptime(f"{date} {val}", '%Y-%m-%d %H:%M:%S')
            if val_time and val_time <= datetime.now():
                return val
            print("\t    That's in the future.")
        except ValueError:
            print("\t    Invalid time.")

        
# if __name__ == '__main__':
#     start()
