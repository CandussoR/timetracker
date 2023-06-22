from datetime import datetime, time
import re
from sqlite3 import Connection
from typing import Literal
from task_data import get_task_rank_from_input

class Input():
    def __init__(self, input_data : str):
        self.input_data = input_data
    
    def is_valid(self, time_measure : Literal["date", "time"]) -> bool:
        format = "%Y-%m-%d" if time_measure == "date" else "%H:%M:%S"

        try:
            if datetime.strptime(self.input_data, format) <= datetime.now():
                return True
            return False
        except ValueError:
            return False

    def is_valid_task(self):
        if self.input_data.isdigit() or self.is_valid("date"):
            raise ValueError

    def parse_string(self):
        if re.search(r'\W', self.input_data):
            task, subtask = re.split('\W', self.input_data, 1)
        return task.title(), subtask.title() if task and subtask else [self.input_data.title()]


def task_string_input() -> str:
    print("Enter a task :")
    while True:
        try:
            task = input("> ")
            if Input(task).is_valid_task():
                return task
        except ValueError :
            print("A task must be a text only string.")

def old_timer_input(connexion : Connection):
    while True:
        task_input = task_string_input()
        (id, task, subtask) = get_task_rank_from_input(connexion, task_input)

        print("Date? (YYYY-MM-DD) > ", end="")
        date = input()

        print("Hour at beginning ? (HH:MM:SS)")
        time_beginning = time_input()

        time_ending = input("Ending ? (HH:MM:SS) \n> ")

        return [id, date, time_beginning, time_ending]

if __name__ == '__main__':
    time_input = Input("23:12:00")
    print(time_input.is_valid("time"))
    date_input = Input("2023-06-02")
    print(date_input.is_valid("date"))