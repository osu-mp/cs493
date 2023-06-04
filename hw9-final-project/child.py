from flask import Blueprint, request, make_response, jsonify, render_template_string
from google.cloud import datastore
import json
import constants
from json2html import *
import re
from utils import error
from db_obj import DB_Obj

from auth import verify_jwt
from users import User

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
        if "name" in content and len(content["name"]) < min_name_length:
            failures.append(f"The name must be at least {min_name_length} characters")
        # TODO : validate birthday
        if "provider_code" in content and len(content["provider_code"]) != provider_code_length:
            failures.append(f"The provider_code must be {provider_code_length} characters")
        if "premature_weeks" in content and \
                (content["premature_weeks"] < min_premature_weeks or content["premature_weeks"] > max_premature_weeks):
            failures.append(f"The age_group must be between {min_premature_weeks} and {max_premature_weeks}")

        if failures:
            return False, "; ".join(failures), 403

        # TODO: future validation, ensure image_url and video_url (if given) point to accessible links
        return True, f"{self.key} validation passed", 200

    def get_all_items(self):
        """
        Get only the children assigned to the logged in user
        Returns:

        """
        query = client.query(kind=constants.users)
        q_limit = constants.pagination_query_limit
        q_offset = int(request.args.get('offset', '0'))
        g_iterator = query.fetch(limit=q_limit, offset=q_offset)
        pages = g_iterator.pages
        results = list(next(pages))
        if g_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?offset=" + str(next_offset)  # + "?limit=" + str(q_limit)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
            e["self"] = self.get_item_self(e.key.id)

        output = {self.key: results}
        if next_url:
            output["next"] = next_url
        output["total_items"] = len(list(query.fetch()))
        return json.dumps(output), 200

@bp.route('', methods=["GET", "POST"])
def response():
    if request.method == "GET":
        try:
            payload = verify_jwt(request)
            print(f"EMAIL {payload['email']}")
            children = User().get_child_ids_of_user(payload['email'])
            print(f"CHILDREN {children}")
        except:
            return error("Unauthorized", 403)


        return Child().get_specific_items(children)
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

    return "Method not recognized", 400

@bp.route('/<id>/users/<user_id>', methods=["PUT", "DELETE"])
def assign_child_to_user(id, user_id):
    # ensure the user id data matches the jwt email data
    payload = verify_jwt(request)
    user_from_db, code = User().get_item_from_db(user_id)
    if code != 200:
        return error("Invalid auth", 401)
    print(f'{user_from_db["email"]=}')
    print(f'{payload["email"]}')
    if user_from_db["email"] != payload["email"]:
        return error("Invalid auth", 403)

    # ensure child exists
    child, code = Child().get_item_from_db(id)
    if code == 404:
        return error("Child not found", 404)

    if request.method == "PUT":
        # ensure child not already assigned to user
        if child["id"] in user_from_db["children"]:
            return error("Child already assigned to user", 403)

        # a child can be assigned multiple users, no need to check further

        key = client.key(constants.users, int(user_id))
        user = client.get(key=key)
        print(f"USER BEFORE {user}")
        user["children"].append(child["id"])
        print(f"USER AFTER {user}")
        client.put(user)
        return "DONE", 204
    elif request.method == "DELETE":
        # ensure child already assigned to user
        if child["id"] not in user_from_db["children"]:
            return error("Child not assigned to user", 403)

        key = client.key(constants.users, int(user_id))
        user = client.get(key=key)
        print(f"USER BEFORE {user}")
        user["children"].remove(child["id"])
        print(f"USER AFTER {user}")
        client.put(user)
        return "DONE", 204

    return "Method not recognized", 400