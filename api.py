import sqlite3
from flask import Flask, g
from flask_restful import Resource, fields, marshal_with, Api
from timer_data import TimeRecord

from timer_stats import total_time

app = Flask(__name__)
api = Api(app)

DATABASE="timer_data.db"

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db

@app.route('/')
def index():
    db = get_db()
    time_year = total_time(db, "year")
    time_week = total_time(db, "week")
    time_day = total_time(db, "today")
    return {"data" : [time_year, time_week, time_day]}

time_record_fields = {
    'id' : fields.Integer,
    'task_id': fields.Integer,
    'date': fields.String,
    'time_beginning' : fields.String,
    'time_ending': fields.String,
    'time_elapsed': fields.String,
    'tag_id': fields.Integer,
    'log': fields.String
}

class TimeRecordResource(Resource):
    @marshal_with(time_record_fields)
    def get(self):
        db = get_db()
        row = db.execute("SELECT * FROM timer_data ORDER BY id DESC LIMIT 1;").fetchone()
        return TimeRecord(*row)
    
# @app.route('/last')
# def display_last_timer():
#     db=get_db()
#     row = db.execute("SELECT * FROM timer_data ORDER BY id DESC LIMIT 1;").fetchone()
#     return TimeRecord(*row)

api.add_resource(TimeRecordResource, '/last')