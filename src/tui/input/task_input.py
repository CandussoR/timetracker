import re
from sqlite3 import Connection
from src.shared.models.task import Task

from src.shared.repositories.task_repository import SqliteTaskRepository

def get_task_rank_from_input(repository : SqliteTaskRepository, task_input : str):
    while True :
        task = parse_input(task_input)
        if task_id := repository.fetch_task_id(task):
            return task_id
        
        add_task = input("\tThe task doesn't exist. Do you want to add it ? (Y/N) > ")
        
        if add_task.upper().strip() == "Y":
            _,_,guid = repository.insert_new_task(task)
            repository.connexion.commit()
            return repository.get_id_from_guid(guid)
        elif add_task.upper().strip() == "N":
            task_input = input("\tEnter the task name again : > ")
            continue
        else :
            print("\tEnter Y for yes or N for no.")
        

def task_string_input(subtask : bool = False) -> str:
    t_or_st = "task" if not subtask else "subtask"
    while True:
        try:
            task_input = input(f"\tEnter a {t_or_st}. > ")
            if re.search(r'\s', task_input):
                print(f"{t_or_st.title()} cannot contain whitespace.")
            # raises ValueError if not int
            elif int(task_input):
                print("\tTask name must be a string.")
        except ValueError :
            return task_input
            

def parse_input(task_input : str) -> Task:
    if re.search(r'\W', task_input):
        task, subtask = re.split(r'\W', task_input, 1)
        return Task(task_name = task, subtask = subtask)    
    else:
        return Task(task_name = task_input)
