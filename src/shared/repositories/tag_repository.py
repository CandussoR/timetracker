from sqlite3 import Connection, connect
from typing import Optional

from src.shared.models.tag import Tag

class SqliteTagRepository():

    def __init__(self, connexion : Optional[Connection], db_name : Optional[str] = None) :
        self.connexion = connexion if connexion is not None else connect(db_name)


    def get_id_from_guid(self, guid : str) -> int:
        '''Only used to insert later in the timer_data table. Returns the id. Do not expose to avoid enumeration exploit.'''
        return self.connexion.execute("SELECT id FROM tags WHERE guid = (?)", [guid]).fetchone()[0]
    

    def all(self) -> list[tuple]:
        return self.connexion.execute("SELECT tag, guid FROM tags;").fetchall()


    def get_by_guid(self, guid : str) -> tuple:
        return self.connexion.execute("SELECT tag, guid FROM tags WHERE guid = ?", [guid]).fetchone()
    

    def create(self, tag : Tag) -> tuple:
        '''Takes a Tag object and returns a (tag, guid) tuple.'''
        return self.connexion.execute( 'INSERT INTO tags (tag, guid) VALUES (:tag, :guid) RETURNING tag, guid;', tag.__dict__).fetchone()
    

    def update(self, tag: Tag) -> tuple:
        '''Takes a Tag object and returns a (tag, guid) tuple.'''
        return self.connexion.execute("UPDATE tags SET tag = :tag WHERE guid = :guid RETURNING tag, guid", tag.__dict__).fetchone()
    

    def delete(self, guid : str) :
        self.connexion.execute("DELETE FROM tags WHERE guid = :guid", [guid])
    

    # TODO : Modify the interface
    # def retrieve_tag_id(self, tag : str) -> int:
    #     try:
    #         return self.check_id_existence(tag)[0]
    #     except TypeError:
    #         # Interface element : get this out of here
    #         print("The tag doesn't exist yet. Adding it...")
    #         return self.insert_new_tag(tag)


    def return_tag_id_if_exists(self, tag : str) -> str:
        '''Only used in the Terminal User Interface.
            Returns an id, or throws a TypeError.'''
        print("tag is ", tag)
        return self.connexion.execute('SELECT id FROM tags WHERE tag=(?);', [tag]).fetchone()[0]


