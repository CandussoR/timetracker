import subprocess
import sys
import os
from src.shared.config.conf import Config
from src.tui.script import start
import src.shared.database.sqlite_db as db
from src.web_api.factory import create_flask_app

def create_app(args : list[str]):
    '''Args are : config file path, [--test], [--api].'''

    conf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "conf.json" if not "--test" in args else "test_conf.json"))
 
    conf = Config(conf_path, is_tui= "--api" not in args)

    if not os.path.exists(conf.log_file):
        subprocess.call(f"mkdir -p {os.path.abspath(os.path.dirname(conf.log_file))}")
        subprocess.call(f"touch {os.path.basename(conf.log_file)}")

    conn = db.connect(conf.database)
    db.create_tables(conn)
    db.set_version(conn)
    conn.commit()
    conn.close()

    if "--api" in args:
        app = create_flask_app(conf)
        app.run(debug=True)

    else:
        start(conf, conf.database)
        

def validate_conf_path(filepath, is_test) :
    if not os.path.isfile(filepath) :
        raise ValueError("Filename doesn't lead to a file")
    if is_test and not filepath.startswith("test_"):
        raise ValueError("Test launch requires a conf filename beginning with 'test_'.")
    return filepath


if __name__ == "__main__":
    create_app(sys.argv[1:])
