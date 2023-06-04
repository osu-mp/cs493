import json
from datetime import datetime
from google.cloud import datastore

client = datastore.Client()

age_groups = [2, 4, 6, 8, 9, 10, 12, 14, 16, 18, 20, 22, 24, 27, 30, 33, 36, 42, 48, 54, 60]

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
    date_object = datetime.strptime(birthday, "%Y-%m-%d")
    difference = datetime.now() - date_object
    months = difference.days * 12 // 365
    print(f"Child is {months} months old")
    for group in sorted(age_groups, reverse=True):
        if months >= group:
            print("Child is in the {group} month age group")
            return group

    raise Exception("Invalid birthday")