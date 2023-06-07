from flask import Blueprint, request
from google.cloud import datastore
import constants
from utils import error
from db_obj import DB_Obj

client = datastore.Client()

bp = Blueprint('activities', __name__, url_prefix='/activities')

max_title_len = constants.max_title_len
max_description_len = constants.max_description_len
min_age_group = 0
max_age_group = max(constants.age_groups)

class Activity(DB_Obj):
    """
    Activity entities that build on basic DB Obj class
    """
    def __init__(self, id=None):
        DB_Obj.__init__(self,
                        id=id,
                        key=constants.activities,
                        required=["title", "description", "age_group", "image_url"],
                        optional=[]
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

        # TODO: future validation, ensure image_url points to accessible links
        return True, f"{self.key} validation passed", 200

    def delete(self):
        """
        When deleting an activity, ensure it is deleted from any children
        that are assigned to it
        Returns:

        """
        if not self.id:
            return error(f"id must be given", 404)

        # remove activity from any children assigned to it
        # default datastore operations do not have a concept of 'contains'
        # so checking each entry like this (slow)
        query = client.query(kind=constants.child)
        children = list(query.fetch())
        for child in children:
            if self.id in child["assigned_activities"]:
                activities = list(child["assigned_activities"])
                activities.remove(self.id)
                child.update({"assigned_activities": activities})
                client.put(child)

        # after cleaning up children, delete the activity from the db
        return super().delete()

@bp.route('', methods=["GET", "POST"])
def response():
    if request.method == "GET":
        return Activity().get_all_items()
    elif request.method == "POST":
        return Activity().create_new(request.get_json())
    else:
        return "Method not recognized", 400

@bp.route('/<id>', methods=["GET", "DELETE", "PUT", "PATCH"])
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