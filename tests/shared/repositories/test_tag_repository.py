import unittest
from src.shared.database import sqlite_db
from src.shared.models.tag import Tag
from src.shared.repositories.tag_repository import SqliteTagRepository
from src.tui.input import tag_input

class TestTagRepository(unittest.TestCase):

    tags = [Tag(tag="Timetracker", guid="1234"), Tag(tag="Python", guid="4567")]

    def setUp(self):
        self.connexion = sqlite_db.connect(':memory:')
        sqlite_db.create_tables(self.connexion)
        self.repo = SqliteTagRepository(self.connexion)
        self.params = [tag.__dict__ for tag in self.tags]
        self.connexion.executemany('''INSERT INTO tags (tag,guid) VALUES (:tag, :guid);''', self.params)
        self.connexion.commit()

    def test_get_all(self):
        result = self.repo.all()
        self.assertEqual(result, [('Timetracker', '1234'), ('Python', '4567')])

    def test_get_by_guid(self):
        result = self.repo.get_by_guid("1234")
        self.assertEqual(result, ('Timetracker', '1234'))

    def test_create(self):
        tag = Tag(tag="API", guid="7890")
        result = self.repo.create(tag)
        self.assertEqual(result, ('API', '7890'))

    def test_update(self):
        tag = Tag(tag="Flask", guid="4567")
        result = self.repo.update(tag)
        self.assertEqual(result, ('Flask', '4567'))

    def test_delete(self):
        self.repo.delete("4567")
        count = self.connexion.execute("SELECT COUNT(*) FROM tags;").fetchone()
        self.assertEqual(count, (1,))
    
    def test_return_tag_id_if_exists(self):
        result = self.repo.return_tag_id_if_exists('Timetracker')
        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()
