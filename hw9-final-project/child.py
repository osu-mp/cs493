from flask import Blueprint, request
from google.cloud import datastore
import json
from utils import error, get_age_group
from db_obj import DB_Obj

from activities import Activity
from auth import verify_jwt
from users import User

import constants

client = datastore.Client()

bp = Blueprint(constants.child, __name__, url_prefix=f'/{constants.child}')

class Child(DB_Obj):
    """
    Child object that builds upon DB Obj class
    """
    def __init__(self, id=None):
        DB_Obj.__init__(self,
                        id=id,
                        key=constants.child,
                        required=["name", "birthday"],
                        optional=["premature_weeks", "provider_code", "assigned_activities"]
                        )

    def validate_values(self, content):
        failures = []
        if len(content["name"]) < constants.min_name_length or len(content["name"]) > constants.max_name_length:
            failures.append(f"The name must be between {constants.min_name_length} and {constants.max_name_length} characters")
        if "birthday" in content:
            try:
                age = get_age_group(content["birthday"])
            except Exception as e:
                failures.append(f"Failed to validate birthday: {e}")
        if "provider_code" in content:
            if len(content["provider_code"]) != constants.provider_code_length:
                failures.append(f"The provider_code must be {constants.provider_code_length} characters")

            # check provider code is unique
            matching_codes = self.get_matching_items({"provider_code": content["provider_code"]})
            if len(matching_codes) > 0:
                failures.append("The provider code is already in use")
        if "premature_weeks" in content and \
                (content["premature_weeks"] < constants.min_premature_weeks or content["premature_weeks"] > constants.max_premature_weeks):
            failures.append(f"The premature_weeks must be between {constants.min_premature_weeks} and {constants.max_premature_weeks}")

        if "assigned_activities" in content:
            for activity_id in list(content["assigned_activities"]):
                item, code = Activity().get_item_from_db(activity_id)
                if code == 404:
                    failures.append(f"Activity with id {activity_id} not found")
        else:
            content["assigned_activities"] = content.get("assigned_activities", [])

        if failures:
            return False, "; ".join(failures), 403

        # TODO: future validation, ensure image_url points to accessible links
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

    def delete(self):
        if not self.id:
            return error(f"id must be given", 404)
        return super().delete()


@bp.route('', methods=["GET", "POST"])
def response():
    if request.method == "GET":
        try:
            payload = verify_jwt(request)
            children = User().get_child_ids_of_user(payload['email'])
        except:
            return error("Unauthorized", 403)


        return Child().get_specific_items(children)
    elif request.method == "POST":
        return Child().create_new(request.get_json())
    else:
        return "Method not recognized", 400

@bp.route('/<id>', methods=["GET", "DELETE", "PUT", "PATCH"])
def child_id(id):
    id = int(id)
    payload = verify_jwt(request)
    email = payload["email"]
    user_details, code =User().get_user_details(email)
    if code != 200:
        return error("Not found", 404)
    if id not in user_details["children"]:
        return error("Not authorized", 403)

    obj = Child(id)
    if not obj:
        return error(f"Child with id {id} not found", 404)

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
        user["children"].append(child["id"])
        client.put(user)
        return "DONE", 204

    elif request.method == "DELETE":
        # ensure child already assigned to user
        if child["id"] not in user_from_db["children"]:
            return error("Child not assigned to user", 403)

        key = client.key(constants.users, int(user_id))
        user = client.get(key=key)
        user["children"].remove(child["id"])
        client.put(user)
        return "DONE", 204

    return "Method not recognized", 400

@bp.route('/<id>/activities/<activity_id>', methods=["PUT", "DELETE"])
def assign_activity(id, activity_id):
    # ensure the user id data matches the jwt email data
    id = int(id)
    activity_id = int(activity_id)

    activity, code = Activity().get_item_from_db(activity_id)
    if code != 200:
        return error("Activity not found", 404)

    payload = verify_jwt(request)
    children_for_user = User().get_child_ids_of_user(payload["email"])
    # child is not assigned to user
    if id not in children_for_user:
        return error("Invalid auth", 403)

    # ensure child exists
    child, code = Child().get_item_from_db(id)
    if code == 404:
        return error("Child not found", 404)

    if request.method == "PUT":
        # ensure child not already assigned activity
        if activity_id in child["assigned_activities"]:
            return error("Activity already assigned to child", 403)

        # a child can be assigned multiple activities, no need to check further

        # ensure activity is correct group for child
        child_age_group = get_age_group(child["birthday"])
        if child_age_group != activity["age_group"]:
            return error(f"Activity age group ({activity['age_group']}) does not agree with child age group ({child_age_group})", 403)

        key = client.key(constants.child, int(child["id"]))
        child = client.get(key=key)
        child["assigned_activities"].append(activity_id)
        client.put(child)
        return "DONE", 204
    elif request.method == "DELETE":
        # ensure child already assigned activity
        if activity_id not in child["assigned_activities"]:
            return error("Activity not assigned to child", 403)

        key = client.key(constants.child, int(child["id"]))
        child = client.get(key=key)
        child["assigned_activities"].remove(activity_id)
        client.put(child)
        return "DONE", 204


    return "Method not recognized", 400