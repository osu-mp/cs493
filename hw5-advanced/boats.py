from flask import Blueprint, request, make_response, jsonify, render_template_string
from google.cloud import datastore
import json
import constants
from utils import *
from json2html import *
import re

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')


@bp.route('', methods=["POST"])
def response():
    if request.method == "POST":
        content = request.get_json()
        return new_boat(content)
    else:
        return "Method not recognized", 400


@bp.route('/<id>', methods=["GET", "DELETE", "PATCH", "PUT"])
def boats_id(id):
    if request.method == "GET":
        if 'application/json' in request.accept_mimetypes:
            return get_single_boat(id)
        elif 'text/html' in request.accept_mimetypes:
            return get_single_boat_html(id)
        else:
            return error("Invalid accept type", 406)
    elif request.method == "DELETE":
        return delete_boat(id)
    elif request.method == "PATCH":
        content = request.get_json()
        return patch_boat(id, content)
    elif request.method == "PUT":
        content = request.get_json()
        return put_boat(id, content)

    else:
        return "Method not recognized", 400


def get_boat_name_unique(name):
    """
    Returns True iff the given boat name is unique (does not already exist in db)
    """
    query = client.query(kind=constants.boats)
    query.add_filter("name", "=", name)
    return len(list(query.fetch())) == 0

def get_boat_name_valid(name):
    """
    Returns True iff the boat name is alphanumeric or spaces and 20 characters or fewer
    """
    if not re.match('[a-zA-Z\s]+$', name):
        return False
    if len(name) > 20:
        return False
    return True

def new_boat(content):
    for key in ["name", "type", "length"]:
        if key not in content:
            return error("The request object is missing at least one of the required attributes", 400)

    if not get_boat_name_unique(content["name"]):
        return error("Boat name already in use", 403)
    if not get_boat_name_valid(content["name"]):
        return error("Boat name invalid. Must be alphanumeric and 20 characters or fewer.", 403)

    new_boat = datastore.entity.Entity(key=client.key(constants.boats))
    new_boat.update({
        "name": content["name"],
        "type": content["type"],
        "length": content["length"],
    })
    client.put(new_boat)
    boat, code = get_single_boat(new_boat.key.id)

    res = make_response(boat)
    res.headers.set('Content-Type', 'application/json')
    res.status_code = 201
    return res


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

    res = make_response("")
    res.headers.set('Content-Type', 'application/json')
    res.status_code = 204
    return res


def patch_boat(id, content):
    if "id" in content:
        return error("You may not edit the boat id", 405)

    boat_key = client.key(constants.boats, int(id))
    boat = client.get(key=boat_key)
    if not boat:
        return error("No boat with this boat_id exists", 404)

    if "name" in content and not get_boat_name_unique(content["name"]):
        return error("Boat name already in use", 405)
    if "name" in content and not get_boat_name_valid(content["name"]):
        return error("Boat name invalid. Must be alphanumeric and 20 characters or fewer.", 403)

    boat = client.get(key=boat_key)
    for key in ["name", "type", "length"]:
        if key in content:
            boat.update({key: content[key]})
    client.put(boat)

    res = make_response(boat)
    res.headers.set('Content-Type', 'application/json')
    res.status_code = 200
    return res

def put_boat(id, content):
    if "id" in content:
        return error("You may not edit the boat id", 405)

    for key in ["name", "type", "length"]:
        if key not in content:
            return error("The request object is missing at least one of the required attributes", 400)

    boat_key = client.key(constants.boats, int(id))
    boat = client.get(key=boat_key)
    if not boat:
        return error("No boat with this boat_id exists", 404)
    if not get_boat_name_valid(content["name"]):
        return error("Boat name invalid. Must be alphanumeric and 20 characters or fewer.", 403)


    if not get_boat_name_unique(content["name"]):
        # if the name is in use, but it is by this boat, that is allowed
        if boat["name"] != content["name"]:
            return error("Boat name already in use", 403)

    boat.update({
        "name": content["name"],
        "type": content["type"],
        "length": content["length"],
    })
    client.put(boat)
    boat, code = get_single_boat(boat.key.id)

    response = jsonify()
    response.status_code = 303
    response.headers['location'] = boat["self"]
    response.autocorrect_location_header = False
    return response


def get_single_boat_html(id):
    boat, code = get_single_boat(id)
    if code != 200:
        return boat, code
    html = render_template_string('''<table>
            <tr>
                <td> Key </td> 
                <td> Value </td>
            </tr>
            <tr>
                <td>id</td>
                <td>{{id}}</td>
            </tr>
            <tr>
                <td>name</td>
                <td>{{name}}</td>
            </tr>
            <tr>
                <td>type</td>
                <td>{{type}}</td>
            </tr>
            <tr>
                <td>length</td>
                <td>{{length}}</td>
            </tr>
            <tr>
                <td>url</td>
                <td>{{url}}</td>
            </tr>
    </table>
''', id=boat['id'], name=boat['name'], type=boat['type'], length=boat['length'], url=boat['self'])
    res = make_response(html)
    res.headers.set('Content-Type', 'text/html')
    res.status_code = 200
    return res
