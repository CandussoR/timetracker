
import dataclasses
import sqlite3
from flask import Flask, g
from flask_restful import Resource, abort, fields, marshal_with, Api
from flask_cors import CORS
from timer_data import TimeRecord

from timer_stats import total_time

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})
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
    
class TimeRecordListResource(Resource):
    @marshal_with(time_record_fields)
    def get(self):
        db=get_db()
        rows = db.execute("SELECT * FROM timer_data ORDER BY id DESC LIMIT 20;").fetchall()
        return [TimeRecord(*row) for row in rows]

api.add_resource(TimeRecordResource, '/last')
api.add_resource(TimeRecordListResource, '/last_twenty')

task_fields = {
    'task_name': fields.String,
    'subtask': fields.String
}

@dataclasses.dataclass
class Task:
    id : int
    task_name : str
    subtask : str

class TaskListResource(Resource):
    @marshal_with(task_fields)
    def get(self):
        db=get_db()
        rows = db.execute("SELECT * FROM tasks ORDER BY id DESC;").fetchall()
        return [Task(*row) for row in rows]
    
class TaskResource(Resource):
    @marshal_with(task_fields)
    def get(self, id_number : int):
        db=get_db()
        row = db.execute("SELECT * FROM tasks WHERE id = ?", [id_number]).fetchone()
        if not row:
            abort(404, joemams="Not found.")
        return Task(*row), 200
    
api.add_resource(TaskListResource, '/tasks')
api.add_resource(TaskResource, '/task/<int:id_number>')

@dataclasses.dataclass
class Tag:
    id : int
    tag : str

tag_fields = {
    'id': fields.Integer,
    'tag': fields.String
}

class TagListResource(Resource):
    @marshal_with(tag_fields)
    def get(self):
        db=get_db()
        row = db.execute("SELECT * FROM tags").fetchone()
        if not row:
            abort(404, joemams="Not found.")
        return Tag(*row), 200


class TagResource(Resource):
    @marshal_with(tag_fields)
    def get(self, id: int):
        db=get_db()
        row = db.execute("SELECT * FROM tags WHERE id = ?", [id]).fetchone()
        if not row:
            abort(404, joemams="Not found.")
        return Tag(*row), 200
    
api.add_resource(TagListResource, "/tags")
api.add_resource(TagResource, "/tag/<int:id>")