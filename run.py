import sys
from src.shared.config.conf import Config
from src.tui.script import start
import src.shared.database.sqlite_db as db
from src.web_api.factory import create_flask_app

def create_app(args : list[str]):
    if "--test" in args:
        try:
            conf = Config("test_conf.json")
        except FileNotFoundError:
            print("No file test_conf.json found at the root of the directory.")
    else:
        conf = Config("conf.json")

    conn = db.connect(conf.local_database)
    db.create_tables(conn)
    conn.commit()
    conn.close()

    if "--api" in args:
        print("Launching an api")
        app = create_flask_app(conf.local_database)
        app.run(debug=True)

    else:
        start(conf, conf.local_database)
        # sync db here after.
        # remote_connexion = db.connect(conf.remote_database)
        

if __name__ == "__main__":
    create_app(sys.argv)
