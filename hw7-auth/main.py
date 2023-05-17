from google.cloud import datastore
from flask import Flask, request, jsonify, _request_ctx_stack
import requests

from functools import wraps
import json

from six.moves.urllib.request import urlopen
from flask_cors import cross_origin
from jose import jwt


import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from werkzeug.exceptions import HTTPException

from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import session
from flask import url_for
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode

import constants
from utils import error, get_single_boat

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

client = datastore.Client()

# Update the values of the following 3 variables
CLIENT_ID = env.get("AUTH0_CLIENT_ID")
CLIENT_SECRET = env.get("AUTH0_CLIENT_SECRET")
DOMAIN = env.get("AUTH0_DOMAIN")
# For example
# DOMAIN = 'fall21.us.auth0.com'

ALGORITHMS = ["RS256"]

oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    api_base_url="https://" + DOMAIN,
    access_token_url="https://" + DOMAIN + "/oauth/token",
    authorize_url="https://" + DOMAIN + "/authorize",
    client_kwargs={
        'scope': 'openid profile email',
    },
server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# This code is adapted from https://auth0.com/docs/quickstart/backend/python/01-authorization?_ga=2.46956069.349333901.1589042886-466012638.1589042885#create-the-jwt-validation-decorator

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

# Verify the JWT in the request's Authorization header
def verify_jwt(request):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[1]
    else:
        raise AuthError({"code": "no auth header",
                            "description":
                                "Authorization header is missing"}, 401)
    
    jsonurl = urlopen("https://"+ DOMAIN+"/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=CLIENT_ID,
                issuer="https://"+ DOMAIN+"/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                            "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                            "description":
                                "incorrect claims,"
                                " please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                            "description":
                                "Unable to parse authentication"
                                " token."}, 401)

        return payload
    else:
        raise AuthError({"code": "no_rsa_key",
                            "description":
                                "No RSA key in JWKS"}, 401)



# Decode the JWT supplied in the Authorization header
@app.route('/decode', methods=['GET'])
def decode_jwt():
    payload = verify_jwt(request)
    return payload          
        

# Generate a JWT from the Auth0 domain and return it
# Request: JSON body with 2 properties with "username" and "password"
#       of a user registered with this Auth0 domain
# Response: JSON with the JWT as the value of the property id_token
@app.route('/login_old', methods=['POST'])
def login_user():
    print("logging in2!")
    content = request.get_json()
    username = content["username"]
    password = content["password"]
    body = {'grant_type':'password','username':username,
            'password':password,
            'client_id':CLIENT_ID,
            'client_secret':CLIENT_SECRET
           }
    headers = { 'content-type': 'application/json' }
    url = 'https://' + DOMAIN + '/oauth/token'
    r = requests.post(url, json=body, headers=headers)
    return r.text, 200, {'Content-Type':'application/json'}

@app.route("/login")
def login():
    print("logging in!")
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.route("/")
def home():
    return render_template("home.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))


def new_boat(content):
    for key in ["name", "type", "length", "public"]:
        if key not in content:
            return error("The request object is missing at least one of the required attributes", 400)

    # if not get_boat_name_unique(content["name"]):
    #     return error("Boat name already in use", 403)
    # if not get_boat_name_valid(content["name"]):
    #     return error("Boat name invalid. Must be alphanumeric and 20 characters or fewer.", 403)

    new_boat = datastore.entity.Entity(key=client.key(constants.boats))
    payload = verify_jwt(request)
    new_boat.update({
        "name": content["name"],
        "type": content["type"],
        "length": content["length"],
        "public": content["public"],
        "owner": get_payload_sub()
    })
    client.put(new_boat)
    boat, code = get_single_boat(new_boat.key.id)

    res = make_response(boat)
    res.headers.set('Content-Type', 'application/json')
    res.status_code = 201
    return res

def get_payload_sub():
    payload = verify_jwt(request)
    return payload["sub"]

def get_all_boats():
    query = client.query(kind=constants.boats)

    try:
        payload = verify_jwt(request)
        query.add_filter("owner", "=", get_payload_sub())
    except:
        query.add_filter("public", "=", True)
    results = list(query.fetch())
    for boat in results:
        boat["id"] = boat.key.id
    return json.dumps(results), 200


@app.route('/boats', methods=["GET", "POST"])
def response():
    if request.method == "GET":
        return get_all_boats()
    elif request.method == "POST":
        content = request.get_json()
        return new_boat(content)
    else:
        return "Method not recognized", 400



@app.route('/boats/<id>', methods=["GET", "DELETE"])
def boats_id(id):
    if request.method == "GET":
        if 'application/json' in request.accept_mimetypes:
            return get_single_boat(id)
        else:
            return error("Invalid accept type", 406)
    elif request.method == "DELETE":
        return delete_boat(id)
    else:
        return "Method not recognized", 400

@app.route('/owners/<id>/boats', methods=["GET"])
def boat_owners(id):
    if request.method == "GET":
        return get_boats_with_owner(id)
    else:
        return "Method not recognized", 400

def get_boats_with_owner(id):
    query = client.query(kind=constants.boats)
    query.add_filter("owner", "=", id)
    query.add_filter("public", "=", True)
    results = list(query.fetch())
    for boat in results:
        boat["id"] = boat.key.id
    return json.dumps(results), 200

def delete_boat(id):
    payload = verify_jwt(request)
    if not id:
        return error("Boat id is required", 403)

    boat, boat_code = get_single_boat(id)

    if boat_code == 404:
        return error("No boat with this boat_id exists", 403)
    if boat["owner"] != get_payload_sub():
        return error("Boat is owned by someone else", 403)

    client.delete(boat)

    res = make_response("")
    res.headers.set('Content-Type', 'application/json')
    res.status_code = 204
    return res

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

