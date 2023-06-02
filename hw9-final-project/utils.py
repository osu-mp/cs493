import json
from google.cloud import datastore

client = datastore.Client()


def error(err_str, code):
    """
    Simplify returning of an error string with response code
    """
    msg = json.dumps({"Error": err_str})
    return msg, code
