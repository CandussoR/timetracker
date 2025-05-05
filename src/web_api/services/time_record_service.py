import datetime
from sqlite3 import Connection
from typing import Optional
from flask import g
from marshmallow import EXCLUDE, ValidationError
from src.shared.models.time_record import TimeRecordInput, TimeRecordResource
from src.shared.repositories.tag_repository import SqliteTagRepository
from src.shared.repositories.task_repository import SqliteTaskRepository
from src.shared.repositories.time_record_repository import SqliteTimeRecordRepository
from src.web_api.schemas.time_record_schema import TimeRecordBeginningRequestSchema, TimeRecordEndingRequestSchema, TimeRecordRequestSchema, TimeRecordSchema
import src.shared.database.sqlite_db as sqlite_db
from werkzeug.datastructures import ImmutableMultiDict

class TimeRecordService():
    def __init__(self, db : str | None = None, connexion : Optional[Connection] = None):
        if connexion is None:
            self.connexion = g._database if db is None else sqlite_db.connect(db)
        else :
            self.connexion = connexion
        self.repo = SqliteTimeRecordRepository(self.connexion)
    

    def get_first_date(self) -> str:
        date, = self.repo.get_first_date();
        return date;

    def get(self, guid : str) -> dict:
        data = self.repo.get(guid)
        if data is None:
            raise ValueError("Ressource cannot be found.")
        else:
            tr = TimeRecordResource(*data)
            return TimeRecordSchema().dump(tr)
    
    def get_by(self, params : dict):
        '''Receives an ImmutableMultiDict in parameter and returns a list of TimeRecords.'''
        # Converting ImmutableMultiDict to dict
        is_multidict = isinstance(params, ImmutableMultiDict)
        conditions = params if not is_multidict else {}
        if not conditions:
            for k in params :
                if k == "week[]":
                    continue
                else:
                    conditions[k] = params[k]
            if "week[]" in params:
                # keeping the camel case to go with rangeBeginning etc.
                # parsing like this for the bindings in the sqlite query and passing the dictionary : less hassle, but coupled
                [conditions["weekStart"], conditions["weekEnd"]] = params.getlist("week[]")

        max_pages = self.repo.get_max_number_of_pages_for_request(conditions)
        # To business
        data = self.repo.get_by(conditions)
        tr = [TimeRecordResource(*d) for d in data]
        return {"pages" : max_pages, "records" : TimeRecordSchema().dump(tr, many=True)}

    def post(self, time_record_type : str, data : dict) -> dict:
        # Forced to use unknown=EXLUDE for Schema validation
        # because it receives task and tag guids and then try to find their IDs. 
        assert self.connexion != None    
        time_record = TimeRecordInput()

        try:
            # Only id used to link between tables.
            if task_guid := data["task_guid"]:
                task_id = SqliteTaskRepository(self.connexion).get_id_from_guid(task_guid)
                if task_id is None:
                    raise ValueError("Guid doesn't exist.")
                time_record.task_id = task_id
            if tag_guid := data["tag_guid"]:
                tag_id = SqliteTagRepository(self.connexion).get_id_from_guid(tag_guid)
                if tag_id is None:
                    raise ValueError("Guid doesn't exist.")
                time_record.tag_id = tag_id
        except KeyError:
            pass

        match time_record_type:
            case "old" :
                TimeRecordRequestSchema().load(data, unknown=EXCLUDE)
                time_record.from_dict(data)
                self.repo.insert_old_timer(time_record)
                self.connexion.commit()
            case "begin" :
                TimeRecordBeginningRequestSchema().load(data, unknown=EXCLUDE)
                time_record.from_dict(data)
                self.repo.insert_beginning(time_record)
                self.connexion.commit()
            case _:
                raise ValidationError("Invalid type.")
        
        return self.get(time_record.guid)
    

    def update(self, operation_type : str, data : dict) -> dict:
        time_record = TimeRecordInput()
        try:
            if task_guid := data["task_guid"]:
                task_repo = SqliteTaskRepository(self.connexion)
                task_id = task_repo.get_id_from_guid(task_guid)
                if task_id is None:
                    raise ValueError("Guid doesn't exist.")
                time_record.task_id = task_id
            if tag_guid := data["tag_guid"]:
                tag_repo = SqliteTagRepository(self.connexion)
                tag_id = tag_repo.get_id_from_guid(tag_guid)
                if tag_id is None:
                    raise ValueError("Guid doesn't exist.")
                time_record.tag_id = tag_id
        except KeyError as e:
            # No tag_guid or task_guid to retrieve, going on with update.
            pass

        match operation_type:
            case "ending" :     
                TimeRecordEndingRequestSchema().load(data, unknown=EXCLUDE)
                time_record.from_dict(data)
                self.repo.update_row_at_ending(time_record)
                self.connexion.commit()
            case "edit" :
                TimeRecordRequestSchema().load(data, unknown=EXCLUDE)
                time_record.from_dict(data)
                self.repo.update_timer(time_record)
                self.repo.update_elapsed_time(time_record)
                self.connexion.commit()

            case _:
                raise ValidationError("Invalid type.")
        return self.get(time_record.guid)
    
    def update_ending_to_now(self):
        self.repo.update_last_row_ending(datetime.datetime.now())
        self.connexion.commit()
