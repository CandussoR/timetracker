import subprocess
import os
import sys
from src.shared.config.conf import Config
import src.shared.database.sqlite_db as db
from src.web_api.factory import create_flask_app

def create_app():
    # Conf path, created by Tauri
    conf_path = os.path.join(os.path.dirname(sys.executable), "resources", "conf.json")
 
    conf = Config(conf_path)

    if not os.path.exists(conf.log_file):
        subprocess.call(f"mkdir -p {os.path.abspath(os.path.dirname(conf.log_file))}")

    conn = db.connect(conf.database)
    db.create_tables(conn)
    db.set_version(conn)
    conn.commit()
    conn.close()

    app = create_flask_app(conf)
    app.run(port=63267, debug=False)
        

def validate_conf_path(filepath, is_test) :
    if not os.path.isfile(filepath) :
        raise ValueError("Filename doesn't lead to a file")
    if is_test and not filepath.startswith("test_"):
        raise ValueError("Test launch requires a conf filename beginning with 'test_'.")
    return filepath


if __name__ == "__main__":
    create_app()
