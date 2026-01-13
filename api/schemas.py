from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ServiceCreate(BaseModel):
    name: str
    IP: str
    frequency_seconds: int
    alerting_window_npings: int


class AdminCreate(BaseModel):
    name: str
    contact_type: str
    contact_value: str


class AdminContactUpdate(BaseModel):
    contact_type: Optional[str] = None
    contact_value: Optional[str] = None


class ServiceAdminUpdate(BaseModel):
    admin_id: int
    role: str  # "primary"/"secondary"


class IncidentCreate(BaseModel):
    service_id: int


class IncidentUpdateStatus(BaseModel):
    status: str


class IncidentUpdateEndedAt(BaseModel):
    ended_at: datetime

class ContactAttemptCreate(BaseModel):
    incident_id: int
    admin_id: int
    attempted_at: datetime
    channel: str
    result: Optional[str] = None
    response_at: Optional[datetime] = None