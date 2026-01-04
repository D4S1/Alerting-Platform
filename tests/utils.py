import jwt
from datetime import datetime, timedelta

JWT_SECRET = "super-secret"

def make_token(incident_id=1, admin_id=1, expired=False):
    payload = {
        "incident_id": incident_id,
        "admin_id": admin_id,
        "exp": datetime.utcnow() - timedelta(minutes=1)
        if expired
        else datetime.utcnow() + timedelta(minutes=10),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
