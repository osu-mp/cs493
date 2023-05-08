import json
import constants
from google.cloud import datastore
from flask import make_response

client = datastore.Client()


def error(err_str, code):
    """
    Simplify returning of an error string with response code
    """
    msg = json.dumps({"Error": err_str})
    return msg, code


def get_boat_self(id):
    return f"{constants.url_root}/boats/{id}"


def get_single_boat(id):
    boat_key = client.key(constants.boats, int(id))
    boat = client.get(key=boat_key)
    if not boat:
        return error("No boat with this boat_id exists", 404)
    boat["id"] = boat.key.id
    boat["self"] = get_boat_self(boat.key.id)
    return boat, 200
