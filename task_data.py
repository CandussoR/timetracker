from sqlite3 import Connection
from input_handlers import Input

CHECK_TASK_EXISTENCE = 'SELECT id FROM tasks WHERE task_name=(?);'

INSERT_NEW_TASK = 'INSERT INTO tasks (task_name) VALUES (?);'

RETRIEVE_RANK ='SELECT * FROM tasks WHERE task_name=(?);'

CHECK_TUPLE_EXISTENCE = 'SELECT id FROM tasks WHERE task_name=(?) AND subtask=(?);'

INSERT_NEW_TUPLE = 'INSERT INTO tasks (task_name, subtask) VALUES (?, ?);'

RETRIEVE_TUPLE_RANK = 'SELECT * FROM tasks WHERE task_name=(?) AND subtask=(?);'


def get_task_rank_from_input(connexion : Connection, task_input : Input):
    task_input = task_input.is_valid_task()
    try:
        check_existence(connexion, *task_input)
        print("The task exists. Getting it's id...")
    except:
        print("The task doesn't exist yet. Adding it...")
        insert_new_task(connexion, *task_input)
    # return fetch_id(connexion, *task_input)
    return fetch_task_rank(connexion, *task_input)

def check_existence(connexion : Connection, *task):
    with connexion:
        if len(task) == 2 :
            result = connexion.execute(CHECK_TUPLE_EXISTENCE, [*task]).fetchone()
        else :
            result = connexion.execute(CHECK_TASK_EXISTENCE, [*task]).fetchone()
    return result[0]

def insert_new_task(connexion : Connection, *task):
    with connexion:
        if len(task) == 2 :
            connexion.execute(INSERT_NEW_TUPLE, [*task])
        else:
            connexion.execute(INSERT_NEW_TASK, [*task])

def fetch_task_rank(connexion : Connection, *task) -> tuple :
    with connexion:
        if len(task) == 2 :
            return connexion.execute(RETRIEVE_TUPLE_RANK, [*task]).fetchone()
        else:
            return connexion.execute(RETRIEVE_RANK, [*task]).fetchone() 

if __name__ == '__main__':
    pass