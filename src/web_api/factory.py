import json
from logging.config import dictConfig
from sqlite3 import Connection
from src.shared.config.conf import Config
import src.shared.database.sqlite_db as sqlite_db
from flask import Flask, g, current_app, request
from flask_cors import CORS
from src.web_api.controllers.time_record_controller import time_records_blueprint
from src.web_api.controllers.task_controller import tasks_blueprint
from src.web_api.controllers.stats_controller import stats_blueprint
from src.web_api.controllers.tag_controller import tag_blueprint
from src.web_api.controllers.settings_controller import settings_blueprint

def create_flask_app(conf : Config) -> Flask:
    # Logger config
    dictConfig({
        "version": 1,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": conf.log_file,
                "maxBytes": 1_048_576,
                "backupCount": 3,
                "encoding": "utf-8",
            }
        },
        "root": {"level": "DEBUG", "handlers": ["file"]},
    })

    app = Flask(__name__)

    app.config.update({"conf" : conf})
    app.config.update(conf.__dict__) 

    # In case multiple processes are using the ports
    cors_allowed = list([f"http://localhost:{num}" for num in range(5173, 5180)])
    cors_allowed.append("http://tauri.localhost")
    CORS(app, origins=cors_allowed)

    @app.before_request
    def get_db():
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite_db.connect(current_app.config['database'])
    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()

    app.register_blueprint(time_records_blueprint)
    app.register_blueprint(tasks_blueprint)
    app.register_blueprint(stats_blueprint)
    app.register_blueprint(tag_blueprint)
    app.register_blueprint(settings_blueprint)

    return app
