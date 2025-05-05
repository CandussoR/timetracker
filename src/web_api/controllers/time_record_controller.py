from traceback import format_exc
from flask import Blueprint, current_app, request
from marshmallow import ValidationError
from src.web_api.services.time_record_service import TimeRecordService

time_records_blueprint = Blueprint("time_records", __name__)


@time_records_blueprint.get('/time_records/first_record_date')
def get_first_date():
    service = TimeRecordService()
    try:
        return service.get_first_date()
    except Exception as e:
        current_app.logger.error(format_exc())
        return str(e), 500

@time_records_blueprint.get("/time_records/<guid>")
def get(guid : str):
    service = TimeRecordService()
    try:
        return service.get(guid)
    except Exception as e:

        current_app.logger.error(format_exc())
        return {"code" : 400, "message" : str(e)}

@time_records_blueprint.get("/time_records")
def get_time_records_by():
    try:
        service = TimeRecordService()
        time_records = service.get_by(request.args)
        return time_records, 200
    except Exception as e:
        current_app.logger.error(format_exc())
        return str(e), 400

@time_records_blueprint.route("/time_records", methods=["POST"])
def create_time_record():
    req = request.get_json()
    operation_type = req["type"]
    data = req["data"]
    try:
        service = TimeRecordService()
        time_record = service.post(operation_type, data)
        return time_record, 200
    except ValidationError as e:
        return str(e), 400
    except ValueError as e:
        return str(e), 400
    except Exception as e:
        current_app.logger.error(format_exc())
        return str(e), 500

@time_records_blueprint.route("/time_records", methods=["PUT"])
def update_time_record():
    req = request.get_json()
    operation_type = req["type"]
    data = req["data"]
    service = TimeRecordService()
    try:
        return service.update(operation_type, data)
    except Exception as e:
        current_app.logger.error(format_exc())
        return str(e), 400

@time_records_blueprint.route("/time_records/last_to_now", methods= ["PUT"])
def update_last_record():
    try:
        TimeRecordService().update_ending_to_now()
        return "OK", 200
    except Exception as e:
        current_app.logger.error(format_exc())
        return str(e), 400