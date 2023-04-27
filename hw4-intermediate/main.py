from flask import Flask
import boats
import loads

"""
CS 493 - HW4 - Marina Intermediate REST API
Matthew Pacey
"""

app = Flask(__name__)
app.register_blueprint(boats.bp)
app.register_blueprint(loads.bp)


@app.route('/')
def index():
    return "Please navigate to /boats or /loads to use this API"


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
