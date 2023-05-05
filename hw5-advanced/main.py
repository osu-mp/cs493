from flask import Flask
import boats

"""
CS 493 - HW5 - Advanced REST API
Matthew Pacey
"""

app = Flask(__name__)
app.register_blueprint(boats.bp)


@app.route('/')
def index():
    return "Please navigate to /boats  to use this API"


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
