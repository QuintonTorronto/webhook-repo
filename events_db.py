from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MongoURL=os.getenv("Mongo_URL")

client = MongoClient(MongoURL)
db=client.github_events
collection=db.events

def save_event(data):
    collection.insert_one(data)

def get_latest_events(limit=20):
    try:
        return list(collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
    except Exception as e:
        print("Error reading from DB:", e)
        return []
    
def is_duplicate(request_id):
    return collection.find_one({"request_id": request_id}) is not None
