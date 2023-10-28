from sqlite3 import Connection


CHECK_TASK_EXISTENCE = 'SELECT id FROM tags WHERE tag=(?);'

INSERT_NEW_TAG = 'INSERT INTO tags (tag) VALUES (?) RETURNING id;'

RETRIEVE_RANK ='SELECT * FROM tags WHERE tag=(?);'

DELETE_RANK = 'DELETE FROM tags WHERE id=(?)'

UPDATE_RANK = 'UPDATE tags SET tag=(?) WHERE id=(?)'

def ask_input() -> str:
    while True:
        try:
            tag_input = input("Enter a tag. > ")
            if int(tag_input):
                print("Tag must be a string.")
        except ValueError :
            return tag_input

def retrieve_tag_id(connexion : Connection, tag : str) -> int:
    try:
        return check_id_existence(connexion, tag)[0]
    except TypeError:
        print("The tag doesn't exist yet. Adding it...")
        return insert_new_tag_return_id(connexion, tag)

def check_id_existence(connexion, tag : str):
    with connexion:
        return connexion.execute(CHECK_TASK_EXISTENCE, [tag]).fetchone()

def insert_new_tag_return_id(connexion : Connection, tag : str) -> int:
    with connexion :
        return connexion.execute(INSERT_NEW_TAG, [tag]).lastrowid