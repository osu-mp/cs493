import json
import constants
from google.cloud import datastore

client = datastore.Client()


def error(err_str, code):
    """
    Simplify returning of an error string with response code
    """
    msg = json.dumps({"Error": err_str})
    return msg, code

def get_load_self(id):
    return f"{constants.url_root}/loads/{id}"

def get_boat_self(id):
    return f"{constants.url_root}/boats/{id}"


def get_single_boat(id):
    boat_key = client.key(constants.boats, int(id))
    boat = client.get(key=boat_key)
    if not boat:
        return error("No boat with this boat_id exists", 404)
    boat["id"] = boat.key.id
    boat["self"] = get_boat_self(boat.key.id)
    boat["loads"] = get_loads_for_boat(id)
    return boat, 200


def get_loads_for_boat(id):
    query = client.query(kind=constants.loads)
    query.add_filter("carrier", "=", id)
    loads = []
    for load in query.fetch():
        loads.append({
            "id": load.key.id,
            "self": get_load_self(load.key.id)
        })

    return loads
