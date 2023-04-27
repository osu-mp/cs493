from flask import Blueprint, request
from google.cloud import datastore
import json
import constants
from utils import *

client = datastore.Client()

bp = Blueprint('loads', __name__, url_prefix='/loads')


@bp.route('', methods=['POST', 'GET'])
def get_loads():
    if request.method == "POST":
        content = request.get_json()
        return post_load(content)
    elif request.method == "GET":
        return get_all_loads()


@bp.route('/<id>', methods=["GET", "DELETE"])
def loads_id(id):
    if request.method == "GET":
        return get_single_load(id)
    elif request.method == "DELETE":
        return delete_load(id)
    else:
        return "Method not recognized", 400


def post_load(content):
    # content = request.get_json()
    for key in ["volume", "item", "creation_date"]:
        if key not in content:
            return error("The request object is missing at least one of the required attributes", 400)

    new_load = datastore.entity.Entity(key=client.key(constants.loads))
    new_load.update({
        "volume": content["volume"],
        "carrier": None,
        "item": content["item"],
        "creation_date": content["creation_date"]
    })
    client.put(new_load)
    new_load, code = get_single_load(new_load.key.id)
    return new_load, 201





def delete_load(id):
    load, code = get_single_load(id)
    if code == 404:
        return error("No load with this load_id exists", 404)

    client.delete(load)
    return "", 204


def get_all_loads():
    query = client.query(kind=constants.loads)
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
    output = {"loads": results}
    if next_url:
        output["next"] = next_url
    return json.dumps(output), 200
