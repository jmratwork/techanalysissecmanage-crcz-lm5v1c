import os
from datetime import datetime
from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
mongo_db = os.environ.get("MONGO_DB", "ng_siem")
mongo_collection = os.environ.get("MONGO_COLLECTION", "scans")
client = MongoClient(mongo_uri)
collection = client[mongo_db][mongo_collection]

@app.route("/scan", methods=["POST"])
def ingest_scan():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    data["received_at"] = datetime.utcnow()
    collection.insert_one(data)
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("INGEST_PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
