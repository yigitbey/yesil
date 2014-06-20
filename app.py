from datetime import datetime
from pymongo import Connection
from flask import Flask, jsonify, request, Response

import settings


app = Flask(__name__)
db = Connection()[settings.DB_NAME]


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


@app.route("/requests", methods=['POST'])
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
    app.run()
