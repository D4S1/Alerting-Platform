import os
from flask import Flask, request, jsonify
from notification_module.notification_engine_cloud_run import NotificationEngine
from notification_module.api_client import NotificationApiClient
from notification_module.mailer import Mailer

app = Flask(__name__)

# Initialize components
api_client = NotificationApiClient(base_url=os.getenv("API_BASE_URL"))
mailer = Mailer()
engine = NotificationEngine(
    api=api_client, 
    mailer=mailer,
    project_id=os.getenv("GCP_PROJECT_ID"),
    location=os.getenv("GCP_LOCATION", "europe-west1"),
    queue=os.getenv("GCP_QUEUE_NAME", "escalation-queue")
)

@app.route("/event", methods=["POST"])
def handle_pubsub_event():
    """Endpoint dla nowych incydentów (np. z Pub/Sub push)"""
    event = request.get_json()
    if not event:
        return "No payload", 400
    
    engine.handle_event(event)
    return "Event processed", 200

@app.route("/escalate", methods=["POST"])
def handle_escalation():
    """Endpoint wywoływany przez Cloud Tasks po X minutach"""
    data = request.get_json()
    incident_id = data.get("incident_id")
    
    if not incident_id:
        return "Missing incident_id", 400
        
    engine.handle_escalation_check(incident_id)
    return "Escalation check completed", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # cloud run uses PORT env variable
    app.run(host="0.0.0.0", port=port)