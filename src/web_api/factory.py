from sqlite3 import Connection, connect
from flask import Flask, g
from flask_cors import CORS
from src.web_api.controllers.time_record_controller import time_records_blueprint
from src.web_api.controllers.task_controller import tasks_blueprint
from src.web_api.controllers.stats_controller import stats_blueprint
from src.web_api.controllers.tag_controller import tag_blueprint

def create_flask_app(db_name : str) -> Flask:
    app = Flask(__name__)
    CORS(app, origins=["http://localhost:5173"])

    @app.before_request
    def get_db():
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = connect(db_name)
            print("We are connected !")
        # return db

    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()
            print("disconnecting")

    app.register_blueprint(time_records_blueprint)
    app.register_blueprint(tasks_blueprint)
    app.register_blueprint(stats_blueprint)
    app.register_blueprint(tag_blueprint)

    return app