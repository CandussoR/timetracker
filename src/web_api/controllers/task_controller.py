import json
from flask import Blueprint, request
from marshmallow import ValidationError

from src.web_api.services.task_service import TaskService

tasks_blueprint = Blueprint("tasks", __name__)


@tasks_blueprint.route("/tasks", methods=["GET"])
def get_all_tasks():
    service = TaskService()
    tasks = service.all()
    return tasks, 200


@tasks_blueprint.route("/task", methods=["POST"])
def create_task():
    service = TaskService()
    data = request.get_json()
    try :
        task = service.post(data)
        return task, 200
    except ValidationError as e:
        return str(e), 400
    except Exception as e:
        return str(e), 500


@tasks_blueprint.route("/task", methods=["PUT"])
def update_task():
    data = request.get_json()
    try:
        task = TaskService().update(data)
        return task, 200
    except ValidationError as e:
        return str(e), 400
    except Exception as e:
        return str(e), 500


@tasks_blueprint.route("/tasks/<guid>", methods=["DELETE"])
def delete_task(guid : str):
    service = TaskService()
    try:
        return service.delete(guid)
    except Exception as e:
        return str(e)