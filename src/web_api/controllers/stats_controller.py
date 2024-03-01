from flask import Blueprint, json, request

from src.web_api.services.stats_service import StatService


stats_blueprint = Blueprint("stats", __name__)

# @stats_blueprint.route("/stats/resume", methods=["GET"])
@stats_blueprint.get("/stats/resume")
def get_home_stats():
    try:
        return  StatService().get_home_stats(), 200
    except Exception as e:
        return str(e), 400

@stats_blueprint.get("/stats/weeks")
def get_week_stats():
    try:
        params = request.args.to_dict()
        return StatService().get_week_total_time(params), 200
    except Exception as e :
        return str(e), 400

@stats_blueprint.get("/stats/task_ratio")
def get_task_time_ratio():
    try:
        params = request.args.to_dict()
        return StatService().get_task_time_ratio(params), 200
    except Exception as e :
        return str(e), 400

@stats_blueprint.get("/stats/generic/week")
def get_generic_week_stats():
    try:
        return StatService().get_generic_week(), 200
    except Exception as e :
        return str(e), 400

@stats_blueprint.get("/stats/generic/month")
def def_generic_month_stats():
    try:
        return StatService().get_generic_month(), 200
    except Exception as e:
        return str(e), 400

@stats_blueprint.get("/stats/generic/year")
def def_generic_year_stats():
    try:
        return StatService().get_generic_year(), 200
    except Exception as e:
        return str(e), 400