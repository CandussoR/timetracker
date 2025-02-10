from sqlite3 import Connection, IntegrityError
from typing import Optional
from flask import g, jsonify
from src.shared.database.sqlite_db import connect
from src.shared.exceptions.unique_constraint import UniqueConstraintError
from src.shared.models.task import Task

class SqliteTaskRepository():
    def __init__(self, connexion : Optional[Connection] = None, db_name : Optional[str] = None) :
        self.connexion = connexion if connexion is not None else connect(db_name)


    def get_tasks(self) -> list[tuple]:
        return self.connexion.execute("SELECT task_name, subtask, guid FROM tasks;").fetchall()


    def get_id_from_guid(self, guid : str) -> int:
        '''Used to convert the GUID received from the API.'''
        return self.connexion.execute("SELECT id FROM tasks WHERE guid = (?)", [guid]).fetchone()[0]


    def fetch_task_id(self, task : Task) -> int :
        if task.subtask :
            query = 'SELECT id FROM tasks WHERE task_name= :task_name AND subtask= :subtask ;'
        else :
            query = 'SELECT id FROM tasks WHERE task_name= :task_name AND subtask IS NULL;'       
        result = self.connexion.execute(query,task.__dict__).fetchone()
        # Just preventing Nonetype exceptions
        return result if not result else result[0]


    def insert_new_task(self, task : Task):
        query = '''INSERT INTO tasks (task_name, subtask, guid) VALUES (:task_name, :subtask, :guid) 
                                        RETURNING task_name, subtask, guid;'''
        return self.connexion.execute(query, task.__dict__).fetchone()

            

    def update(self, task : Task) -> tuple:
        '''Returns (task_name, subtask, guid).'''
        query = '''UPDATE tasks
                    SET task_name = :task_name, subtask = :subtask
                    WHERE guid = :guid
                    RETURNING task_name, subtask, guid;'''
        return self.connexion.execute(query, task.__dict__).fetchone()
         

    def delete_task(self, guid : str) :
        return self.connexion.execute('DELETE FROM tasks WHERE guid=(?)', [guid])


if __name__ == '__main__':
    pass
