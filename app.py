from datetime import datetime
from pymongo import Connection
from flask import Flask, jsonify, request, Response

import settings
from helpers import sha1_string, force_unicode, force_utf8

from flask import jsonify
import time
import uuid

from functools import wraps

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

app = Flask(__name__)
db = Connection()[settings.DB_NAME]

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

def assert_if(condition, error_message):
    if not condition:
        raise InvalidUsage(error_message)


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    user_name = data.get('user_name')
    password = data.get('password')
    email = data.get('email')
    assert_if(user_name and len(user_name) > 3 and len(user_name) < 20, "username len >= 4 and < 20 ")
    assert_if(password and len(password) >= 5 and len(password) < 20, "password len > 5 and < 20 ")
    assert_if(email and len(email) >= 3 and len(email) < 50 and '@' in email, "email needed ")

    # check unique
    assert_if(not db.users.find_one(dict(user_name=user_name)), "username not unique")
    assert_if(not db.users.find_one(dict(email=email)), "email not unique")

    hashed_password = sha1_string(force_utf8(password) + "users")
    token = sha1_string(str(uuid.uuid4()))
    user = db.users.insert(dict(
        user_name = user_name,
        email = email,
        password = hashed_password,
        token = token
    ))

    return jsonify(user_name=user_name, token=token)


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    password = data.get('password')
    user_name = data.get('user_name')
    assert_if(user_name, 'username needed')
    assert_if(password, 'password needed')

    hashed_password = sha1_string(force_utf8(password) + "users")

    #
    user = db.users.find_one(dict(
        user_name = user_name,
        password = hashed_password
    ))

    assert_if(user, "password or user_name wrong")

    return jsonify(user_name=user_name, token=user['token'])


def require_user(fn):
    @wraps(fn)
    def inner():
        try:
            token = request.json['token']
        except:
            token = request.args.get('token')

        assert_if(token, 'token needed for this action')
        user = db.users.find_one(dict(token=token))
        assert_if(user, "token is wrong")
        return fn(user)
    return inner


@app.route('/check_token', methods=['POST'])
@require_user
def check_token(user):
    return Response(status=200)

@app.route('/check_token2', methods=['POST'])
@require_user
def check_token2(user):
    return Response(status=200)


@app.route("/heartbeat", methods=['POST'])
def heartbeat():
    data = request.json
    access_token = data.get('access_token')
    device_id = data.get('device_id')
    location = data.get('location')

    if not device_id and not access_token:
        return Response(status=400)

    if device_id:
        filters = {
            "device_id": device_id
        }
    else:
        filters = {
            "access_token": access_token
        }

    existing_activity = db.activity.find_one(filters)

    if existing_activity:

        db.activity.update(filters, {
            "$set": {
                "location": location,
                "last_seen": datetime.now()
            }
        })

        return Response(status=202)

    bundle = {
        "location": location,
        "last_seen": datetime.now()
    }

    bundle.update(filters)

    db.activity.insert(bundle)

    return Response(status=201)


@app.route("/requests", methods=['GET'])
def get_requests():
    return jsonify({
        "objects": []
    })


@app.route("/requests", methods=['POST'])
def post_requests():
    return jsonify({
        "objects": []
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

