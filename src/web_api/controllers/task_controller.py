from sqlite3 import IntegrityError
from traceback import format_exc
from flask import Blueprint, current_app, request
from marshmallow import ValidationError

from src.shared.exceptions.unique_constraint import UniqueConstraintError
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
    except UniqueConstraintError as e:
        return str(e), 422
    except Exception as e:
        current_app.logger.error(format_exc())
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
        current_app.logger.error(format_exc())
        return str(e), 500


@tasks_blueprint.route("/task/<guid>", methods=["DELETE"])
def delete_task(guid : str):
    service = TaskService()
    try:
        return service.delete(guid)
    except IntegrityError as e:
        return "The task couldn't be deleted because it is linked to existing timers.", 400
    except Exception as e:
        current_app.logger.error(format_exc())
        return str(e), 500