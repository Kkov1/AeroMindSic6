from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017")
db = client["sic"]
collection = db["assignment"]

@app.route('/', methods=['POST'])
def insert():
    try:
        data = request.get_json()
        collection.insert_one(data)
        return jsonify({
            "message": "Berhasil disimpan"
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)