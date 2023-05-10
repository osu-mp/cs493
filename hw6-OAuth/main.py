import json
import flask
import requests
import uuid

from constants import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, oauth_uri, SCOPE, state_key
from flask import Flask, render_template, request, session, redirect, url_for
from google.cloud import datastore


client = datastore.Client()

app = Flask(__name__)


"""
CS 493 - HW6 - OAuth 2.0 Implementation
Matthew Pacey
"""

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())


@app.route('/', methods=["POST", "GET"])
def index():
    if request.method == "POST":
        proceed = request.form.get('proceed')
        if proceed == 'yep':
            return redirect(url_for('oauth'))

    if 'credentials' not in session:
        return render_template('index.html')

    credentials = json.loads(flask.session['credentials'])
    if credentials['expires_in'] <= 0:
        return redirect(url_for('oauth'))
    else:
        headers = {
            'Authorization': f'Bearer {credentials["access_token"]}'
        }
        req_uri = 'https://people.googleapis.com/v1/people/me?personFields=names'
        r = requests.get(req_uri, headers=headers)
        user_info = json.loads(r.text)
        return render_template(
            'oauth.html',
            name=user_info["names"][0]["givenName"],
            family=user_info["names"][0]["familyName"],
            state=session['state']
        )


@app.route('/oauth')
def oauth():
    if 'code' not in request.args:
        state = generate_state()
        auth_uri = f"{oauth_uri}?"
        data = {
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'response_type': 'code',
            'scope': SCOPE,
            'state': state,
        }
        for key in data:
            auth_uri += f"{key}={data[key]}&"

        return redirect(auth_uri)
    else:
        auth_code = request.args.get('code')
        returned_state = request.args.get('state')
        if not check_state_exists(returned_state):
            return "The given state does not exist, your request has been rejected", 401
        data = {
            'code': auth_code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        r = requests.post('https://oauth2.googleapis.com/token', data=data)
        session['credentials'] = r.text
        session['state'] = returned_state
        return redirect(url_for('index'))


def generate_state():
    """
    Generate a new state name and store in datastore
    Return the generated state (will be passed to oauth)
    """
    state = str(uuid.uuid4())
    # TODO store to datastore
    entry = datastore.entity.Entity(key=client.key(state_key))
    entry.update({
        "state": state
    })
    client.put(entry)
    return state

def check_state_exists(state):
    """
    Return True iff the given state exists in datastore
    """
    query = client.query(kind=state_key)
    query.add_filter("state", "=", state)
    return list(query.fetch()) != []


if __name__ == '__main__':
    app.secret_key = str(uuid.uuid4())
    app.debug = True
    app.run()#host='127.0.0.1', port=8080, debug=True)

