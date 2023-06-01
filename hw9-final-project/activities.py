from flask import Blueprint, request, make_response, jsonify, render_template_string
from google.cloud import datastore
import json
import constants
from json2html import *
import re

client = datastore.Client()

bp = Blueprint('activities', __name__, url_prefix='/activities')


@bp.route('', methods=["POST"])
def response():
    if request.method == "POST":
        return "HEY"
    else:
        return "Method not recognized", 400
