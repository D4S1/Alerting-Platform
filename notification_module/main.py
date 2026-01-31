import os
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
    esc_delay_seconds=300,
    project_id=os.environ.get("GCP_PROJECT_ID"),
    location=os.environ.get("GCP_LOCATION", "europe-cemtral2"),
    queue=os.environ.get("GCP_QUEUE_NAME", "escalation-queue")
)

# -----------------------------
# Flask endpoints
# -----------------------------

@app.route("/event", methods=["POST"])
def handle_pubsub_event():
    """Endpoint for new incidents (e.g. from Pub/Sub push)"""
    event = request.get_json()
    if not event:
        return "No payload", 400
    
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
    port = int(os.environ.get("PORT", 8080))  # PORT env variable for Cloud Run
    app.run(host="0.0.0.0", port=port)