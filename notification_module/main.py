import os
import base64
import json
from flask import Flask, request, jsonify
from notification_module.notification_engine import NotificationEngine
from notification_module.api_client import NotificationApiClient
from notification_module.mailer import Mailer

app = Flask(__name__)

# -----------------------------
# Component intitialization
# -----------------------------

api_client = NotificationApiClient(base_url=os.environ.get("API_BASE_URL"))
mailer = Mailer()
engine = NotificationEngine(
    api=api_client, 
    mailer=mailer,
    esc_delay_seconds=300
)

# -----------------------------
# Flask endpoints
# -----------------------------

@app.route("/event", methods=["POST"])
def handle_pubsub_event():
    """Endpoint for new incidents (e.g. from Pub/Sub push)"""
    envelope = request.get_json()
    if not envelope:
        return "No payload", 400

    # Pub/Sub message should have 'message' key
    if "message" not in envelope:
        print("Invalid Pub/Sub envelope", envelope)
        return "Invalid envelope", 400

    pubsub_message = envelope["message"]

    if "data" in pubsub_message:
        try:
            # Decode base64 -> bytes -> string -> json
            data_str = base64.b64decode(pubsub_message["data"]).decode("utf-8")
            event = json.loads(data_str)
        except Exception as e:
            print(f"Failed to decode message: {e}")
            return "Decoding error", 400
    else:
        return "No data in message", 400
    
    print(f"Processing event: {event}")  # Logging for debugging
    engine.handle_event(event)
    return "Event processed", 200

@app.route("/escalate", methods=["POST"])
def handle_escalation():
    """Endpoint called by Cloud Tasks after escalation delay to check for acknowledgment"""
    data = request.get_json()
    incident_id = data.get("incident_id")
    
    if not incident_id:
        return "Missing incident_id", 400
        
    engine.handle_escalation_check(incident_id)
    return "Escalation check completed", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)