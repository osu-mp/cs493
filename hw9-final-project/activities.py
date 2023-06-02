from flask import Blueprint, request, make_response, jsonify, render_template_string
from google.cloud import datastore
import json
import constants
from json2html import *
import re
from utils import error
from db_obj import DB_Obj

client = datastore.Client()

bp = Blueprint('activities', __name__, url_prefix='/activities')

max_title_len = 40
max_description_len = 300
min_age_group = 0
max_age_group = 60

class Activity(DB_Obj):
    def __init__(self, id=None):
        DB_Obj.__init__(self,
                        id=id,
                        key=constants.activities,
                        required=["title", "description", "age_group", "image_url"],
                        optional=["video_url"]
                        )

    def validate_values(self, content):
        failures = []
        if "title" in content and len(content["title"]) > max_title_len:
            failures.append(f"Character limit of {max_title_len} for title exceeded")
        if "description" in content and len(content["description"]) > max_description_len:
            failures.append(f"Character limit of {max_description_len} for description exceeded")
        if "age_group" in content and \
                (content["age_group"] < min_age_group or content["age_group"] > max_age_group):
            failures.append(f"The age_group must be between {min_age_group} and {max_age_group}")

        if failures:
            return False, "; ".join(failures), 403

        # TODO: future validation, ensure image_url and video_url (if given) point to accessible links
        return True, f"{self.key} validation passed", 200

@bp.route('', methods=["GET", "POST"])
def response():
    if request.method == "GET":
        return Activity().get_all_items()
    elif request.method == "POST":
        return Activity().create_new(request.get_json())
    else:
        return "Method not recognized", 400

@bp.route('/<id>', methods=["GET", "DELETE", "PUT", "PATCH"])
def activity_id(id):
    obj = Activity(id)
    if not obj:
        return error(f"Activity with id {id} not found", 404)

    if request.method == "GET":
        return obj.get_item_from_db(id)
    elif request.method == "DELETE":
        return obj.delete()
    elif request.method == "PUT":
        return obj.put_item(id, request.get_json())
    elif request.method == "PATCH":
        return obj.patch_item(id, request.get_json())