from flask import Blueprint, request
from marshmallow import ValidationError

from src.web_api.services.tag_service import TagService


tag_blueprint = Blueprint("tag", __name__)


@tag_blueprint.route("/tags", methods=["GET"])
def get_tags():
    try:
        tags = TagService().get_all()
        return tags, 200
    except Exception as e:
        return str(e), 400
    

@tag_blueprint.route("/tag/<guid>", methods=["GET"])
def get_tag(guid : str):
    try:
        tag = TagService().get_tag_by_guid(guid)
        return tag, 200
    except ValueError as e:
        return str(e), 404
    except Exception as e:
        return str(e), 500


@tag_blueprint.route("/tag", methods=["POST"])
def create_tag():
    try:
        data = request.get_json()
        tag = TagService().new(data)
        return tag
    except ValidationError as e:
        return str(e), 400
    except Exception as e :
        return str(e), 500


@tag_blueprint.route("/tag", methods=["PUT"])
def update_tag():
    try:
        data = request.get_json()
        tag = TagService().update(data)
        return tag
    except ValidationError as e:
        return str(e), 400
    except Exception as e :
        return str(e), 500

    
@tag_blueprint.route("/tag/<guid>", methods=["DELETE"])
def delete_tag(guid : str):
    try:
        TagService().delete(guid)
        return "Deleted", 200
    except Exception as e:
        return str(e), 400