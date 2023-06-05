import json
from datetime import datetime
from google.cloud import datastore

import constants

client = datastore.Client()

def error(err_str, code):
    """
    Simplify returning of an error string with response code
    """
    msg = json.dumps({"Error": err_str})
    return msg, code

def get_age_group(birthday):
    """
    Given a birthday, return the corresponding age group
    Args:
        birthday:

    Returns:

    """

    try:
        date_object = datetime.strptime(birthday, constants.date_format)
    except ValueError:
        raise Exception(f"Incorrect birthday, expected in format {constants.date_format}")

    now = datetime.now()
    if constants.DEBUG:
        now = datetime.strptime(constants.debug_date, constants.date_format)

    difference = now - date_object
    months = difference.days * 12 // 365
    print(f"Child is {months} months old")
    if months > constants.max_age:
        raise Exception(f"Child is too old, max age is {constants.max_age} months")
    for group in sorted(constants.age_groups, reverse=True):
        if months >= group:
            print(f"Child is in the {group} month age group")
            return group

    raise Exception(f"Invalid birthday, the age does not fall into one of the following month groups {age_groups}")