from traceback import format_exc
from flask import Blueprint, current_app, g, json, request

from src.web_api.services.stats_service import BaseStatService, CustomStatService, MonthStatService, StatServiceFactory, WeekStatService, YearStatService


stats_blueprint = Blueprint("stats", __name__)

@stats_blueprint.get("/stats/resume")
def get_home_stats():
    try:
        return  BaseStatService().get_home_stats(), 200
    except Exception as e:
        current_app.logger.error(format_exc())
        return str(e), 400


@stats_blueprint.get("/stats/task_ratio")
def get_task_time_ratio():
    try:
        req = request.args
        service = StatServiceFactory().create_stat_service(g._database, req)
        return service.get_task_time_ratio(), 200
    except Exception as e :
        current_app.logger.error(format_exc())
        return str(e), 400

@stats_blueprint.get("/stats/generic")
def get_generic_stats():
    try:
        req = request.args
        service = StatServiceFactory().create_stat_service(g._database, request.args)
        return service.get_generic_stat(req["date"] if "date" in req else None), 200 # type: ignore
    except Exception as e:
        current_app.logger.error(format_exc())
        return str(e), 400


@stats_blueprint.post("/stats/generic/custom")
def get_custom_stats():
    try:
        return CustomStatService(g._database, request.get_json()["params"]).get_custom_stats()
    except Exception as e:
        current_app.logger.error(format_exc())
        return str(e), 500