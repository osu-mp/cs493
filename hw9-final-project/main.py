from flask import Flask
from email_validator import validate_email, EmailNotValidError

import activities
"""
CS 493 - Final Project - REST API for Early Childhood Development App
Matthew Pacey
"""

app = Flask(__name__)
app.register_blueprint(activities.bp)
# app.register_blueprint(boats.bp)

"""
TODO
Status Codes
Your application should support at least the following status codes.

200
201
204
401
403
405
406
"""

@app.route('/')
def index():
    output = "TODO<br>"
    emails = ["my+address@example.org", "myaddress@example2.org", "@invalid.com"]
    for email in emails:
        try:
            emailinfo = validate_email(email, check_deliverability=False)

            # After this point, use only the normalized form of the email address,
            # especially before going to a database query.
            output += f"{email} : {emailinfo.normalized}<br>"
        except:
            output += f"{email} : FAILED<br>"
    return output


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
