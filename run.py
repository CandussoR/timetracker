import sys
import os
from src.shared.config.conf import Config
from src.tui.script import start
import src.shared.database.sqlite_db as db
from src.web_api.factory import create_flask_app

def create_app(args : list[str]):
    '''Args are : config file path, [--test], [--api].'''

    conf_file = validate_conf_path(args[0], is_test=False)
    
    conf = Config(conf_file)

    conn = db.connect(conf.local_database)
    db.create_tables(conn)
    conn.commit()
    conn.close()

    if "--api" in args:
        app = create_flask_app(conf.local_database)
        app.run(debug=True)

    else:
        start(conf, conf.local_database)
        

def validate_conf_path(filepath, is_test) :
    if not os.path.isfile(filepath) :
        raise ValueError("Filename doesn't lead to a file")
    if is_test and not filepath.startswith("test_"):
        raise ValueError("Test launch requires a conf filename beginning with 'test_'.")
    return filepath


if __name__ == "__main__":
    create_app(sys.argv[1:])
