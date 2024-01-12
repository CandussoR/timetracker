import json
from flask import g
from src.shared.models.task import Task

from src.shared.repositories.task_repository import SqliteTaskRepository
from src.web_api.schemas.task_schema import TaskSchema, UlidSchema


class TaskService():
    def __init__(self) :
        self.connexion = g._database
        self.repo = SqliteTaskRepository(self.connexion)


    def all(self) -> list[TaskSchema]:
        return [Task(*row) for row in self.repo.get_tasks()]
    

    def post(self, data : dict):
        schema = TaskSchema().load(data)
        task = Task().from_dict(schema)
        created = self.repo.insert_new_task(task)
        self.connexion.commit()
        return TaskSchema().dump(created)
    

    def update(self, data : dict):
        TaskSchema().load(data)
        task = Task(**data)
        updated = self.repo.update(task)
        self.connexion.commit()
        return TaskSchema().dump(Task(*updated))
    

    def delete(self, guid : dict):
        UlidSchema().load({"guid" : guid})
        self.repo.delete_task(guid)
        self.connexion.commit()
        # Update SQLITE_SEQUENCE ?
        return "Successfully deleted."