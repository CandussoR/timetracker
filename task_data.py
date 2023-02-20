import re

CHECK_TASK_EXISTENCE = 'SELECT id FROM tasks WHERE task_name=(?);'

INSERT_NEW_TASK = 'INSERT INTO tasks (task_name) VALUES (?);'

RETRIEVE_ID ='SELECT id FROM tasks WHERE task_name=(?);'

CHECK_TUPLE_EXISTENCE = 'SELECT id FROM tasks WHERE task_name=(?) AND subtask=(?);'

INSERT_NEW_TUPLE = 'INSERT INTO tasks (task_name, subtask) VALUES (?, ?);'

RETRIEVE_TUPLE_ID = 'SELECT id FROM tasks WHERE task_name=(?) AND subtask=(?);'


def task_input_to_id(connexion):
    task_input = task_string_input()
    task_input = parse_input(task_input)
    try:
        check_existence(connexion, *task_input)
        print("The task exists. Getting it's id...")
    except:
        print("The task doesn't exist yet. Adding it...")
        insert_new_task(connexion, *task_input)
    return fetch_id(connexion, *task_input) 

def task_string_input():
    while True:
        try:
            task_input = input("Enter a task. > ")
            if int(task_input):
                print("Task name must be a string.")
        except ValueError :
            return task_input
            
def parse_input(task_input : str):
    if re.search(r'\W', task_input):
        task, subtask = re.split('\W', task_input, 1)
        return task.title(), subtask.title()
    else:
        return [task_input.title()]

def check_existence(connexion, *task):
    with connexion:
        if len(task) == 2 :
            result = connexion.execute(CHECK_TUPLE_EXISTENCE, [*task]).fetchone()
        else :
            result = connexion.execute(CHECK_TASK_EXISTENCE, [*task]).fetchone()
    return result[0]

def insert_new_task(connexion, *task):
    with connexion:
        if len(task) == 2 :
            connexion.execute(INSERT_NEW_TUPLE, [*task])
        else:
            connexion.execute(INSERT_NEW_TASK, [*task])

def fetch_id(connexion, *task):
    with connexion:
        if len(task) == 2 :
            retrieved_id = connexion.execute(RETRIEVE_TUPLE_ID, [*task]).fetchone()
        else:
            retrieved_id = connexion.execute(RETRIEVE_ID, [*task]).fetchone()
    return retrieved_id[0]

if __name__ == '__main__':
    import sqlite_db as db
    connexion = db.connect('timer_data.db')

    # print(parse_input("Code.Lecture"))
    # print(parse_input("Code"))
    task_input = task_input_to_id(connexion)
    print(task_input)