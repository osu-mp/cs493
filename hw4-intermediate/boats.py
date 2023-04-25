from flask import Blueprint, request
from google.cloud import datastore
import json
import constants
from utils import *
from loads import get_single_load

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')


@bp.route('', methods=["POST", "GET"])
def response():
    if request.method == "POST":
        content = request.get_json()
        return new_boat(content)
    elif request.method == "GET":
        return get_all_boats()
    else:
        return "Method not recognized", 400


@bp.route('/<id>', methods=["GET", "DELETE"])
def boats_id(id):
    if request.method == "GET":
        return get_single_boat(id)
    elif request.method == "DELETE":
        return delete_boat(id)
    else:
        return "Method not recognized", 400


@bp.route('/<boat_id>/loads/<load_id>', methods=["PUT", "DELETE"])
def assign_load(boat_id, load_id):
    if request.method == "PUT":
        return assign_load_to_boat(boat_id, load_id)
    elif request.method == "DELETE":
        return delete_load_from_boat(boat_id, load_id)
    else:
        return "Method not recognized", 400


@bp.route('/<boat_id>/loads', methods=["GET"])
def get_boat_loads(boat_id):
    if request.method == "GET":
        boat, code = get_single_boat(boat_id)
        if code == 404:
            return error("No boat with this boat_id exists", 404)
        loads = {"loads":  []}
        for load in get_loads_for_boat(boat_id):
            id = load["id"]
            full_load = get_single_load(id)
            loads["loads"].append(full_load)
        return loads, 200
    else:
        return "Method not recognized", 400

def new_boat(content):
    for key in ["name", "type", "length"]:
        if key not in content:
            return error("The request object is missing at least one of the required attributes", 400)
    new_boat = datastore.entity.Entity(key=client.key(constants.boats))
    new_boat.update({
        "name": content["name"],
        "type": content["type"],
        "length": content["length"],
        "loads": [],
    })
    client.put(new_boat)
    new_boat["id"] = new_boat.key.id
    new_boat["self"] = get_boat_self(new_boat.key.id)
    return new_boat, 201


def get_all_boats():
    query = client.query(kind=constants.boats)
    q_limit = int(request.args.get('limit', '3'))
    q_offset = int(request.args.get('offset', '0'))
    g_iterator = query.fetch(limit=q_limit, offset=q_offset)
    pages = g_iterator.pages
    results = list(next(pages))
    if g_iterator.next_page_token:
        next_offset = q_offset + q_limit
        next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
    else:
        next_url = None
    for e in results:
        e["id"] = e.key.id
    output = {"boats": results}
    if next_url:
        output["next"] = next_url
    return json.dumps(output), 200


def delete_boat(id):
    boat, boat_code = get_single_boat(id)

    if boat_code == 404:
        return error("No boat with this boat_id exists", 404)

    client.delete(boat)

    # if the boat had any loads, unload those from the boat
    query = client.query(kind=constants.loads)
    query.add_filter("carrier", "=", id)
    for load in query.fetch():
        load["carrier"] = None
        client.put(load)

    return "DONE", 204


def assign_load_to_boat(boat_id, load_id):
    boat, code = get_single_boat(boat_id)
    load, load_code = get_single_load(load_id)
    if code != 200 or load_code != 200:
        return error("The specified boat and/or load does not exist", 404)

    # see if load already exists
    if load["carrier"] != None:
        return error("The load is already loaded on another boat", 403)

    load["carrier"] = boat_id
    client.put(load)
    return "DONE", 204


def delete_load_from_boat(boat_id, load_id):
    boat, code = get_single_boat(boat_id)
    load, load_code = get_single_load(load_id)

    if code != 200 or load_code != 200:
        return error("No boat with this boat_id is loaded with the load with this load_id", 404)

    if not load["carrier"] or load["carrier"]["id"] != boat_id:
        return error("No boat with this boat_id is loaded with the load with this load_id", 404)

    load["carrier"] = None
    client.put(load)
    return "DONE", 204

