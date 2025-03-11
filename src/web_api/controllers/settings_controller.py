from flask import Blueprint, current_app, request, g
import os
import shutil
from src.shared.config.conf import Config
import posixpath

from src.web_api.services.settings_service import update_settings

settings_blueprint = Blueprint('settings', __name__)

@settings_blueprint.get('/settings')
def get_conf():
    return {
        "database" : current_app.config["database"],
        "timer_ring": current_app.config["timer_sound_path"]
    }, 200

@settings_blueprint.put('/settings')
def update_conf():
    conf = Config(current_app.config["conf"])
    args = request.get_json()
    try:
        update_settings(args, conf)
        return {
            "database" : current_app.config["database"],
            "timer_ring": current_app.config["timer_sound_path"]
        }, 200
    except Exception as e:
        return str(e), 400