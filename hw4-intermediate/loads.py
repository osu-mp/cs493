from flask import Blueprint, request
from google.cloud import datastore
import json
import constants
from utils import *

client = datastore.Client()

bp = Blueprint('guest', __name__, url_prefix='/loads')



@bp.route('', methods=['POST','GET'])
def get_loads():
    if request.method == "POST":
        content = request.get_json()
        for key in ["volume", "item", "creation_date"]:
            if key not in content:
                return error("The request object is missing at least one of the required attributes", 400)

        load = datastore.entity.Entity(key=client.key(constants.loads))
        load.update({
            "volume": content["volume"],
            "carrier": None,
            "item": content["item"],
            "creation_date": content["creation_date"]
        })
        client.put(load)
        load["id"] = load.key.id
        load["self"] = get_load_self(load.key.id)
        return load, 201
    elif request.method == "GET":
        pass


def get_carrier_info(load):
    boat_id = load["carrier"]
    if boat_id == None:
        return None
    boat, code = get_single_boat(boat_id)
    boat_info = {
        "id": boat_id,
        "name": boat["name"],
        "self": get_boat_self(boat_id)
    }
    return boat_info

def get_single_load(id):
    key = client.key(constants.loads, int(id))
    load = client.get(key=key)
    if not load:
        return error("No load with this load_id exists", 404)
    load["id"] = int(load.key.id)
    load["self"] = get_load_self(id)
    load["carrier"] = get_carrier_info(load)
    return load, 200

@bp.route('/<id>', methods=["GET", "PATCH", "DELETE"])
def slips_id(id):
    if request.method == "GET":
        return get_single_load(id)
    elif request.method == "PATCH":
        content = request.get_json()
        return edit_single_boat(id, content)
    elif request.method == "DELETE":
        return delete_slip(id)
    else:
        return "Method not recognized", 400
