from google.cloud import datastore
from flask import Flask, render_template, request
import json
import constants

"""
CS 493 - HW3 - Marina REST API
Matthew Pacey
"""

app = Flask(__name__)
ds_client = datastore.Client()


def new_boat(content):
    for key in ["name", "type", "length"]:
        if key not in content:
            return error("The request object is missing at least one of the required attributes", 400)
    new_boat = datastore.entity.Entity(key=ds_client.key(constants.boats))
    new_boat.update({
        "name": content["name"],
        "type": content["type"],
        "length": content["length"]
    })
    ds_client.put(new_boat)
    new_boat["id"] = new_boat.key.id
    return new_boat, 201


def get_single_boat(id):
    boat_key = ds_client.key(constants.boats, int(id))
    boat = ds_client.get(key=boat_key)
    if not boat:
        return error("No boat with this boat_id exists", 404)
    boat["id"] = boat.key.id
    return boat, 200


def edit_single_boat(id, content):
    for key in ["name", "type", "length"]:
        if key not in content:
            return error("The request object is missing at least one of the required attributes", 400)

    boat_key = ds_client.key(constants.boats, int(id))
    boat = ds_client.get(key=boat_key)
    if not boat:
        return error("No boat with this boat_id exists", 404)

    boat = ds_client.get(key=boat_key)
    boat.update({
        "name": content["name"],
        "type": content["type"],
        "length": content["length"]
    })
    ds_client.put(boat)
    return boat, 200


def delete_boat(id):
    boat, boat_code = get_single_boat(id)

    if boat_code == 404:
        return error("No boat with this boat_id exists", 404)

    ds_client.delete(boat)

    # if the boat was in a slip, remove that entry
    query = ds_client.query(kind=constants.slips)
    results = list(query.fetch())
    for slip in results:
        if slip["current_boat"] == int(id):
            slip["current_boat"] = None
            ds_client.put(slip)
            break               # should only be in one slip, can stop here

    return "", 204


def new_slip(content):
    if "number" not in content:
        return error("The request object is missing the required number", 400)
    new_slip = datastore.entity.Entity(key=ds_client.key(constants.slips))
    new_slip.update({
        "number": content["number"],
        "current_boat": None,
    })
    ds_client.put(new_slip)
    new_slip["id"] = int(new_slip.key.id)
    return new_slip, 201


def get_single_slip(id):
    slip_key = ds_client.key(constants.slips, int(id))
    slip = ds_client.get(key=slip_key)
    if not slip:
        return error("No slip with this slip_id exists", 404)
    slip["id"] = int(slip.key.id)
    if slip["current_boat"]:
        slip["current_boat"] = int(slip["current_boat"])
    return slip, 200


def delete_slip(id):
    slip, slip_code = get_single_slip(id)

    if slip_code == 404:
        return error("No slip with this slip_id exists", 404)

    ds_client.delete(slip)
    return "", 204

def boat_arrives(slip_id, boat_id):
    boat, boat_code = get_single_boat(boat_id)
    slip, slip_code = get_single_slip(slip_id)

    if boat_code == 404 or slip_code == 404:
        return error("The specified boat and/or slip does not exist", 404)

    if slip["current_boat"] != None:
        return error("The slip is not empty", 403)

    slip["current_boat"] = boat_id
    ds_client.put(slip)
    return "", 204



def remove_boat_from_slip(slip_id, boat_id):
    boat, boat_code = get_single_boat(boat_id)
    slip, slip_code = get_single_slip(slip_id)

    if boat_code == 404 or slip_code == 404:
        # return error("The specified boat and/or slip does not exist", 404)
        return error("No boat with this boat_id is at the slip with this slip_id", 404)

    if slip["current_boat"] == None or slip["current_boat"] != boat_id:
        return error("No boat with this boat_id is at the slip with this slip_id", 404)

    slip["current_boat"] = None
    ds_client.put(slip)
    return "", 204


def error(err_str, code):
    """
    Simplify returning of an error string with response code
    """
    msg = json.dumps({"Error": err_str})
    return msg, code


@app.route('/')
def index():
    return "Please navigate to /boats or /slips to use this API"


@app.route('/boats', methods=["POST", "GET"])
def response():
    if request.method == "POST":
        content = request.get_json()
        return new_boat(content)
    elif request.method == "GET":
        query = ds_client.query(kind=constants.boats)
        results = list(query.fetch())
        for boat in results:
            boat["id"] = boat.key.id
        return json.dumps(results)
    else:
        return "Method not recognized", 400


@app.route('/boats/<id>', methods=["GET", "PATCH", "DELETE"])
def boats_id(id):
    if request.method == "GET":
        return get_single_boat(id)
    elif request.method == "PATCH":
        content = request.get_json()
        return edit_single_boat(id, content)
    elif request.method == "DELETE":
        return delete_boat(id)
    else:
        return "Method not recognized", 400


@app.route('/slips', methods=['POST', 'GET'])
def slips():
    if request.method == "POST":
        content = request.get_json()
        return new_slip(content)
    elif request.method == "GET":
        query = ds_client.query(kind=constants.slips)
        results = list(query.fetch())
        for slip in results:
            slip["id"] = slip.key.id
        return json.dumps(results)
    else:
        return "Method not recognized", 400

@app.route('/slips/<id>', methods=["GET", "PATCH", "DELETE"])
def slips_id(id):
    if request.method == "GET":
        return get_single_slip(id)
    elif request.method == "PATCH":
        content = request.get_json()
        return edit_single_boat(id, content)
    elif request.method == "DELETE":
        return delete_slip(id)
    else:
        return "Method not recognized", 400


@app.route('/slips/<slip_id>/<boat_id>', methods=["PUT", "DELETE"])
def boat_arrive_at_slip(slip_id, boat_id):
    if slip_id:
        slip_id = int(slip_id)
    if boat_id:
        boat_id = int(boat_id)

    if request.method == "PUT":
        return boat_arrives(slip_id, boat_id)

    elif request.method == "DELETE":
        return remove_boat_from_slip(slip_id, boat_id)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
