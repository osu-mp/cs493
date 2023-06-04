from flask import Blueprint, request, make_response, jsonify, render_template_string
from google.cloud import datastore
import json
import constants
from json2html import *
import re
from utils import error
from db_obj import DB_Obj

from auth import verify_jwt

client = datastore.Client()

bp = Blueprint(constants.users, __name__, url_prefix=f'/{constants.users}')

max_title_len = 40
max_description_len = 300
min_age_group = 0
max_age_group = 60

class User(DB_Obj):
    def __init__(self, id=None):
        DB_Obj.__init__(self,
                        id=id,
                        key=constants.users,
                        required=["email"],
                        optional=["children", "ignore_activities"]
                        )

    def validate_values(self, content):
        # TODO validation
        return True, f"{self.key} validation passed", 200

    def get_user_details(self, email):
        query = client.query(kind=self.key)
        query.add_filter("email", "=", email)
        results = list(query.fetch())

        if not results:
            return error("User not found", 404)
        # should not hit this
        # if len(results) > 1:
        #     return error("Too many users found", 401)
        id = int(results[0].key.id)
        return self.get_item_from_db(id)


    def get_child_ids_of_user(self, email):
        """
        Given the users email address, return the list of children assigned to it
        Args:
            email:

        Returns:

        """
        query = client.query(kind=self.key)
        query.add_filter("email", "=", email)
        results = list(query.fetch())

        if not results:
            return []
        print(f'PACEY {results[0]["children"]}')
        # return [5880693565423616, 5399054188019712]

        id = int(results[0].key.id)
        return list(results[0]["children"])

@bp.route('', methods=["GET", "POST"])
def response():
    print("GET USERS")

    if request.method == "GET":
        return User().get_all_items()
    elif request.method == "POST":
        payload = verify_jwt(request)
        content = request.get_json()
        if payload["email"] != content["email"]:
            return error("Mismatch between email and JWT, local user not created", 403)
        content["children"] = []
        content["ignore_activities"] = []
        return User().create_new(content)
    else:
        return "Method not recognized", 400

@bp.route('/<id>', methods=["GET", "DELETE", "PUT", "PATCH"])
def activity_id(id):
    payload = verify_jwt(request)
    obj = User(id)
    if not obj:
        return error(f"User with id {id} not found", 404)

    if request.method == "GET":
        return obj.get_item_from_db(id)
    elif request.method == "DELETE":
        return obj.delete()
    elif request.method == "PUT":
        return obj.put_item(id, request.get_json())
    elif request.method == "PATCH":
        return obj.patch_item(id, request.get_json())