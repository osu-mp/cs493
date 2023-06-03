from flask import Blueprint, request, make_response, jsonify, render_template_string
from google.cloud import datastore
import json
import constants
from json2html import *
import re
from utils import error
from db_obj import DB_Obj

client = datastore.Client()

bp = Blueprint(constants.child, __name__, url_prefix=f'/{constants.child}')

min_name_length = 2
min_premature_weeks = 0
max_premature_weeks = 40
provider_code_length = 6

class Child(DB_Obj):
    def __init__(self, id=None):
        DB_Obj.__init__(self,
                        id=id,
                        key=constants.child,
                        required=["name", "birthday"],
                        optional=["premature_weeks", "provider_code"]
                        )

    def validate_values(self, content):
        failures = []
        if "name" in content and len(content["name"]) > min_name_length:
            failures.append(f"The name must be at least {min_name_length} characters")
        # TODO : validate birthday
        if "provider_code" in content and len(content["provider_code"]) != provider_code_length:
            failures.append(f"The provider_code must be {provider_code_length} characters")
        if "premature_weeks" in content and \
                (content["premature_weeks"] < min_premature_weeks or content["premature_weeks"] > max_premature_weeks):
            failures.append(f"The age_group must be between {min_age_group} and {max_age_group}")

        if failures:
            return False, "; ".join(failures), 403

        # TODO: future validation, ensure image_url and video_url (if given) point to accessible links
        return True, f"{self.key} validation passed", 200

@bp.route('', methods=["GET", "POST"])
def response():
    if request.method == "GET":
        return Child().get_all_items()
    elif request.method == "POST":
        return Child().create_new(request.get_json())
    else:
        return "Method not recognized", 400

@bp.route('/<id>', methods=["GET", "DELETE", "PUT", "PATCH"])
def activity_id(id):
    obj = Child(id)
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