from flask import Blueprint


stats_blueprint = Blueprint("stats", __name__)

@stats_blueprint.route("/stats/resume", methods=["GET"])
def get_home_stats():
    return "number of timers and total hours, flow style."