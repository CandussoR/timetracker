from sqlite3 import Connection


CHECK_TASK_EXISTENCE = 'SELECT id FROM tags WHERE tag=(?);'

INSERT_NEW_TASK = 'INSERT INTO tags (tag) VALUES (?);'

RETRIEVE_RANK ='SELECT * FROM tags WHERE tag=(?);'

DELETE_RANK = 'DELETE FROM tags WHERE id=(?)'

UPDATE_RANK = 'UPDATE tags SET tag=(?) WHERE id=(?)'

def ask_input(connexion : Connection):
    tag_input = parse_input(tag_input)
    try:
        check_existence(connexion, *tag_input)
        print("The tag exists. Getting it's id...")
    except:
        print("The tag doesn't exist yet. Adding it...")
        insert_new_tag(connexion, *tag_input)
    # return fetch_id(connexion, *task_input)
    return fetch_tag_rank(connexion, *tag_input)