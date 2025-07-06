from flask import Flask, request, jsonify
from datetime import datetime, timezone
from events_db import save_event, get_latest_events, is_duplicate
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return 'Webhook Receiver Running!'

@app.route('/github-event', methods=['POST'])
def github_event():
    try:
        payload = request.json
        event_type = request.headers.get('X-GitHub-Event')
        result = {}

        if event_type == "push":
            commit_hash = payload.get("head_commit", {}).get("id", "unknown")
            result = {
                "request_id": commit_hash,
                "author": payload.get("pusher", {}).get("name", "unknown"),
                "action": "push",
                "from_branch": None,
                "to_branch": payload.get("ref", "").split("/")[-1],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        elif event_type == "pull_request":
            pr = payload.get("pull_request", {})
            action = payload.get("action")
            sha = pr.get("head", {}).get("sha", "unknown")

            if action == "opened":
                result = {
                    "request_id": sha,
                    "author": pr.get("user", {}).get("login", "unknown"),
                    "action": "pull_request",
                    "from_branch": pr.get("head", {}).get("ref", ""),
                    "to_branch": pr.get("base", {}).get("ref", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

            elif action == "closed" and pr.get("merged"):
                result = {
                    "request_id": pr.get("merge_commit_sha", sha),
                    "author": pr.get("user", {}).get("login", "unknown"),
                    "action": "merge",
                    "from_branch": pr.get("head", {}).get("ref", ""),
                    "to_branch": pr.get("base", {}).get("ref", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

        if result:
            if not is_duplicate(result["request_id"]):
                save_event(result)
                return jsonify({"status": "event saved", "data": result}), 200
            else:
                return jsonify({"status": "duplicate", "request_id": result["request_id"]}), 200

        return jsonify({"status": "event ignored"}), 200

    except Exception as e:
        print(" Exception occurred:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/events', methods=['GET'])
def get_events():
    events = get_latest_events()
    return jsonify(events)
