from flask import Blueprint, g, json, request

from src.web_api.services.stats_service import BaseStatService, MonthStatService, StatServiceFactory, WeekStatService, YearStatService


stats_blueprint = Blueprint("stats", __name__)

# @stats_blueprint.route("/stats/resume", methods=["GET"])
@stats_blueprint.get("/stats/resume")
def get_home_stats():
    try:
        return  BaseStatService().get_home_stats(), 200
    except Exception as e:
        return str(e), 400

@stats_blueprint.get("/stats/weeks")
def get_week_stats():
    try:
        params = request.args.to_dict()
        return StatServiceFactory().create_stat_service(g._database, request.args).get_week_total_time_per_week_for_years(params), 200
    except Exception as e :
        return str(e), 400

@stats_blueprint.get("/stats/task_ratio")
def get_task_time_ratio():
    print("in controller")
    try:
        params = request.args.to_dict()
        return StatServiceFactory().create_stat_service(g._database, request.args).get_task_time_ratio(), 200
    except Exception as e :
        return str(e), 400

@stats_blueprint.get("/stats/generic/week")
def get_generic_week_stats():
    try:
        return WeekStatService(g._database).get_generic_stat(), 200
    except Exception as e :
        return str(e), 400


@stats_blueprint.get("/stats/generic/month")
def def_generic_month_stats():
    try:
        return MonthStatService(g._database).get_generic_stat(), 200
    except Exception as e:
        return str(e), 400

@stats_blueprint.get("/stats/generic/year")
def def_generic_year_stats():
    try:
        return YearStatService(g._database).get_generic_stat(), 200
    except Exception as e:
        return str(e), 400


@stats_blueprint.get("/stats/generic/custom")
def get_custom_stats():
    try:
        return BaseStatService().get_custom_stats(request.args)
    except Exception as e:
        return str(e), 500