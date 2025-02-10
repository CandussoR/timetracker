import sqlite3
from flask import g
from src.shared.exceptions.unique_constraint import UniqueConstraintError
from src.shared.models.tag import Tag
from src.shared.repositories.tag_repository import SqliteTagRepository
from src.web_api.schemas.tag_schema import TagSchema
from src.web_api.schemas.task_schema import UlidSchema


class TagService():
    def __init__(self, conn : sqlite3.Connection | None = None) :
        self.connexion = conn if conn else g._database 
        self.repo = SqliteTagRepository(self.connexion)


    def get_all(self):
        data = self.repo.all()
        tags = [Tag(*tag) for tag in data]
        return TagSchema(many=True).dump(tags)
    

    def get_tag_by_guid(self, guid : str) :
        UlidSchema().load({"guid" : guid})
        retrieved = self.repo.get_by_guid(guid)
        if retrieved is None:
            raise ValueError("Ressource not found.")
        return TagSchema().dump(Tag(*retrieved))


    def new(self, data : dict):
        TagSchema().load(data)
        tag = Tag().from_dict(data)
        try:
            created = self.repo.create(tag)
            self.connexion.commit()
            return TagSchema().dump(Tag(*created))
        except sqlite3.IntegrityError:
            raise UniqueConstraintError("This tag already exists.")
    

    def update(self, data : dict):
        TagSchema().load(data)
        tag = Tag().from_dict(data)
        updated = self.repo.update(tag)
        self.connexion.commit()
        return TagSchema().dump(Tag(*updated))
    

    def delete(self, guid : str) :
        UlidSchema().load({"guid" : guid})
        self.repo.delete(guid)
        self.connexion.commit()
        return "Successfully deleted."
