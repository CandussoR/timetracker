from sqlite3 import connect
from sqlite3.dbapi2 import Connection
from typing import Optional

from flask import g
from src.shared.models.time_record import TimeRecordInput
from datetime import datetime

class SqliteTimeRecordRepository():


    def __init__(self, connexion : Optional[Connection] = None, db_name : Optional[str] = None) :
        self.connexion = connexion if connexion is not None else connect(db_name)


    def get(self, guid : str) -> tuple:
        query = '''SELECT td.guid,
                          tasks.task_name,
                          tasks.subtask,
                          date, 
                          time_beginning, 
                          time_ending, 
                          tags.tag,
                          log
                   FROM timer_data td
                   JOIN tasks ON tasks.id = td.task_id
                   LEFT JOIN tags ON tags.id = td.tag_id
                   WHERE td.guid = (?);'''
        return self.connexion.execute(query, [guid]).fetchone()
    
    def get_by(self, conditions : dict) -> list[tuple]:
        keys = conditions.keys()
        parameters = []
        try:
            if "date" in keys:
                parameters.append("date = (:date)")
            if set(["weekStart", "weekEnd"]).issubset(keys):
                parameters.append(f"date BETWEEN (:weekStart) AND (:weekEnd)")
            if set(["rangeBeginning", "rangeEnd"]).issubset(keys):
                parameters.append("date BETWEEN (:rangeBeginning) AND (:rangeEnd)")
            if "year" in keys :
                year = conditions["year"]
                like = f"'{year}%'"
                parameters.append(f"date LIKE {like}")
            if "month" in keys:
                month = conditions["month"]
                like = f"'{month}%'"
                parameters.append(f"date LIKE {like}")

            if "task" in keys and not "subtask" in keys:
                parameters.append("tasks.task_name = (:task)")
            elif set(["task", "subtask"]).issubset(keys):
                parameters.append("tasks.task_name = (:task) AND tasks.subtask = (:subtask)")
                
            if "tag" in keys:
                parameters.append("tags.tag = (:tag)")
        except Exception as e:
            print(e)

        query = f'''SELECT td.guid,
                          tasks.task_name,
                          tasks.subtask,
                          date, 
                          time_beginning, 
                          time_ending, 
                          tags.tag, 
                          log  
                   FROM timer_data td
                   JOIN tasks ON tasks.id = td.task_id
                   LEFT JOIN tags ON tags.id = td.tag_id
                   WHERE {' AND '.join(parameters)}'''
        return self.connexion.execute(query, conditions).fetchall()

    def insert_beginning(self, record: TimeRecordInput) -> int:
        '''Returns the guid of the inserted time record.'''
        query = '''INSERT INTO timer_data (task_id, date, time_beginning, tag_id, guid) 
                    VALUES (:task_id, date(:date), time(:time_beginning), :tag_id, :guid)
                    RETURNING guid;'''
        return self.connexion.execute(query, record.__dict__).fetchone()


    def insert_old_timer(self, record : TimeRecordInput) -> str:
        '''Returns the guid of the inserted time record.'''
        query = '''
                INSERT INTO timer_data (task_id, date, time_beginning, time_ending, tag_id, log, guid)
                VALUES  (:task_id, date(:date), time(:time_beginning), time(:time_ending), :tag_id, :log, :guid)
                RETURNING guid;
                '''
        self.connexion.execute(query, record.__dict__)
        self.update_elapsed_time(record)
        return record.guid
    
    
    def update_timer(self, record : TimeRecordInput) -> tuple:
        query = '''UPDATE timer_data
                   SET task_id = :task_id,
                       date = :date,
                       time_beginning = :time_beginning,
                       time_ending = :time_ending,
                       tag_id = COALESCE(:tag_id, tag_id),
                       log = COALESCE(:log, log)
                   WHERE guid = :guid
                   RETURNING *'''
        return self.connexion.execute(query, record.__dict__).fetchone()


    def update_row_at_ending(self, record : TimeRecordInput):
        self.add_time_ending_and_log(record)
        self.update_elapsed_time(record)


    def add_time_ending_and_log(self, record : TimeRecordInput):
        query = '''UPDATE timer_data 
                                SET time_ending=time(:time_ending), log=(:log)
                                WHERE guid = (:guid);'''
        self.connexion.execute(query, record.__dict__) 


    def update_elapsed_time(self, record : TimeRecordInput) -> int:
        query = '''UPDATE timer_data
                                SET time_elapsed = CASE
                                        WHEN (strftime('%s',time_ending) - strftime('%s',time_beginning)) > 0 
                                            THEN (strftime('%s',time_ending) - strftime('%s',time_beginning))
                                            ELSE (strftime('%s',time_ending) - strftime('%s',time_beginning)) + 86400
                                        END
                                WHERE guid = (?)
                                RETURNING time_elapsed;'''
        return self.connexion.execute(query, [record.guid]).fetchone()        


    def update_last_row_ending(self, time : datetime):
        row = self.connexion.execute("SELECT guid FROM timer_data ORDER BY id DESC LIMIT 1").fetchone()
        record = TimeRecordInput(guid=row[0], time_ending = time)
        query = '''UPDATE timer_data 
                            SET time_ending = time(:time_ending)
                            WHERE guid = (:guid);'''
        self.connexion.execute(query, record.__dict__)
        self.update_elapsed_time(record)