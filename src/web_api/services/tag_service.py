from flask import g
from src.shared.models.tag import Tag
from src.shared.repositories.tag_repository import SqliteTagRepository
from src.web_api.schemas.tag_schema import TagSchema
from src.web_api.schemas.task_schema import UlidSchema


class TagService():
    def __init__(self) :
        self.connexion = g._database
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
        created = self.repo.create(tag)
        self.connexion.commit()
        return TagSchema().dump(Tag(*created))
    

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
