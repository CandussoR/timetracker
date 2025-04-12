import sys
import os
from src.tui.script import start
from src.shared.config.conf import Config
import src.shared.database.sqlite_db as db

def create_app():
    '''Args are : config file path, [--test], [--api].'''

    conf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "conf.json"))
 
    conf = Config(conf_path)

    conn = db.connect(conf.database)
    db.create_tables(conn)
    conn.commit()
    conn.close()

    start(conf, conf.database)
        

def validate_conf_path(filepath, is_test) :
    if not os.path.isfile(filepath) :
        raise ValueError("Filename doesn't lead to a file")
    if is_test and not filepath.startswith("test_"):
        raise ValueError("Test launch requires a conf filename beginning with 'test_'.")
    return filepath


if __name__ == "__main__":
    create_app()
